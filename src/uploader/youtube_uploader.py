"""YouTube video upload module."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeUploader:
    """Upload videos to YouTube."""

    def __init__(self) -> None:
        """Initialize YouTube uploader."""
        self.client_id = settings.youtube_client_id
        self.client_secret = settings.youtube_client_secret
        self.credentials: Optional[Credentials] = None
        self.youtube = None

    def authenticate(self, credentials_path: Optional[Path] = None) -> None:
        """Authenticate with YouTube API.

        Args:
            credentials_path: Path to saved credentials
        """
        try:
            # Try to load existing credentials
            if credentials_path and credentials_path.exists():
                self.credentials = Credentials.from_authorized_user_file(
                    str(credentials_path), SCOPES
                )
                logger.info("Loaded existing YouTube credentials")

            # If no valid credentials, initiate OAuth flow
            if not self.credentials or not self.credentials.valid:
                logger.info("Starting YouTube OAuth flow...")

                client_config = {
                    "installed": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uris": [settings.youtube_redirect_uri],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                }

                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                self.credentials = flow.run_local_server(port=8080)

                # Save credentials for future use
                if credentials_path:
                    with open(credentials_path, "w") as f:
                        f.write(self.credentials.to_json())
                    logger.info(f"Saved YouTube credentials to {credentials_path}")

            # Build YouTube API client
            self.youtube = build("youtube", "v3", credentials=self.credentials)
            logger.info("YouTube API client initialized successfully")

        except Exception as e:
            logger.error(f"Error authenticating with YouTube: {e}")
            raise

    async def upload_video(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: List[str],
        category_id: str = "28",  # Science & Technology
        privacy_status: str = "public",
        publish_at: Optional[datetime] = None,
    ) -> Dict[str, str]:
        """Upload video to YouTube.

        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags
            category_id: YouTube category ID
            privacy_status: Privacy status (public, private, unlisted)
            publish_at: Scheduled publish time (for private videos)

        Returns:
            Dictionary with video ID and URL
        """
        if not self.youtube:
            raise ValueError("YouTube client not initialized. Call authenticate() first.")

        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        try:
            # Prepare video metadata
            body = {
                "snippet": {
                    "title": title[:100],  # YouTube title limit
                    "description": description[:5000],  # YouTube description limit
                    "tags": tags[:500],  # YouTube allows up to 500 tags
                    "categoryId": category_id,
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False,
                },
            }

            # Add scheduled publish time if provided
            if publish_at and privacy_status == "private":
                body["status"]["publishAt"] = publish_at.isoformat()

            # Create media upload
            media = MediaFileUpload(
                str(video_path),
                chunksize=1024 * 1024,  # 1MB chunks
                resumable=True,
                mimetype="video/*",
            )

            # Execute upload
            logger.info(f"Starting upload: {title}")
            request = self.youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media,
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"Upload progress: {progress}%")

            video_id = response["id"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            logger.info(f"Video uploaded successfully: {video_url}")

            return {
                "id": video_id,
                "url": video_url,
            }

        except Exception as e:
            logger.error(f"Error uploading video to YouTube: {e}")
            raise

    async def set_thumbnail(self, video_id: str, thumbnail_path: Path) -> bool:
        """Set custom thumbnail for video.

        Args:
            video_id: YouTube video ID
            thumbnail_path: Path to thumbnail image

        Returns:
            True if successful
        """
        if not self.youtube:
            raise ValueError("YouTube client not initialized")

        if not thumbnail_path.exists():
            raise FileNotFoundError(f"Thumbnail not found: {thumbnail_path}")

        try:
            media = MediaFileUpload(str(thumbnail_path), mimetype="image/jpeg")

            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=media,
            ).execute()

            logger.info(f"Thumbnail set for video {video_id}")
            return True

        except Exception as e:
            logger.error(f"Error setting thumbnail: {e}")
            return False

    async def get_video_analytics(self, video_id: str) -> Dict:
        """Get analytics data for a video.

        Args:
            video_id: YouTube video ID

        Returns:
            Dictionary with analytics data
        """
        if not self.youtube:
            raise ValueError("YouTube client not initialized")

        try:
            response = self.youtube.videos().list(
                part="statistics,contentDetails",
                id=video_id,
            ).execute()

            if not response.get("items"):
                logger.warning(f"Video not found: {video_id}")
                return {}

            item = response["items"][0]
            stats = item.get("statistics", {})

            analytics = {
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "duration": item.get("contentDetails", {}).get("duration", ""),
            }

            logger.info(f"Retrieved analytics for video {video_id}")
            return analytics

        except Exception as e:
            logger.error(f"Error getting video analytics: {e}")
            return {}
