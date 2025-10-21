"""Video editing and generation module."""

from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

import numpy as np
from moviepy.editor import (
    VideoClip,
    ImageClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    ColorClip,
)
from moviepy.video.fx import fadein, fadeout
from PIL import Image, ImageDraw, ImageFont

from src.core.config import get_settings
from src.core.logging import get_logger
from src.utils.helpers import ensure_directory

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class VideoScene:
    """Video scene data structure."""

    image_path: Path
    duration: float
    text_overlay: Optional[str] = None
    transition: str = "fade"


class VideoEditor:
    """Video editor for creating YouTube videos."""

    def __init__(self) -> None:
        """Initialize video editor."""
        self.width, self.height = self._parse_resolution(settings.video_resolution)
        self.fps = settings.video_fps

    def _parse_resolution(self, resolution: str) -> Tuple[int, int]:
        """Parse resolution string to width and height.

        Args:
            resolution: Resolution string like "1920x1080"

        Returns:
            Tuple of (width, height)
        """
        parts = resolution.split("x")
        return int(parts[0]), int(parts[1])

    async def create_intro(
        self,
        title: str,
        duration: float = 5.0,
    ) -> VideoClip:
        """Create intro clip with title.

        Args:
            title: Video title
            duration: Intro duration in seconds

        Returns:
            Intro video clip
        """
        # Create background
        background = ColorClip(
            size=(self.width, self.height),
            color=(20, 20, 40),
            duration=duration,
        )

        # Create title text
        try:
            title_clip = TextClip(
                title,
                fontsize=70,
                color="white",
                font="Arial-Bold",
                size=(self.width - 200, None),
                method="caption",
            ).set_position("center").set_duration(duration)

            # Add fade in/out
            title_clip = fadein(title_clip, 1.0)
            title_clip = fadeout(title_clip, 1.0)

            # Composite
            intro = CompositeVideoClip([background, title_clip])

            logger.info(f"Created intro clip: {duration}s")
            return intro

        except Exception as e:
            logger.error(f"Error creating intro: {e}")
            # Return simple background if text fails
            return background

    async def create_outro(
        self,
        duration: float = 5.0,
    ) -> VideoClip:
        """Create outro clip with call-to-action.

        Args:
            duration: Outro duration in seconds

        Returns:
            Outro video clip
        """
        # Create background
        background = ColorClip(
            size=(self.width, self.height),
            color=(40, 20, 20),
            duration=duration,
        )

        try:
            # Subscribe message
            subscribe_text = TextClip(
                "チャンネル登録をお願いします！",
                fontsize=60,
                color="white",
                font="Arial-Bold",
            ).set_position("center").set_duration(duration)

            subscribe_text = fadein(subscribe_text, 1.0)

            outro = CompositeVideoClip([background, subscribe_text])

            logger.info(f"Created outro clip: {duration}s")
            return outro

        except Exception as e:
            logger.error(f"Error creating outro: {e}")
            return background

    async def create_scene_from_image(
        self,
        image_path: Path,
        duration: float,
        text_overlay: Optional[str] = None,
    ) -> VideoClip:
        """Create video scene from image.

        Args:
            image_path: Path to image file
            duration: Scene duration in seconds
            text_overlay: Optional text to overlay

        Returns:
            Video clip
        """
        try:
            # Load and resize image
            img_clip = ImageClip(str(image_path)).set_duration(duration)

            # Resize to fit while maintaining aspect ratio
            img_clip = img_clip.resize(height=self.height)

            # Center crop if wider than target
            if img_clip.w > self.width:
                img_clip = img_clip.crop(
                    x_center=img_clip.w / 2,
                    width=self.width,
                )

            # Add text overlay if provided
            if text_overlay:
                text_clip = TextClip(
                    text_overlay,
                    fontsize=40,
                    color="white",
                    bg_color="rgba(0,0,0,0.5)",
                    font="Arial-Bold",
                    size=(self.width - 100, None),
                    method="caption",
                ).set_position(("center", "bottom")).set_duration(duration)

                img_clip = CompositeVideoClip([img_clip, text_clip])

            # Add fade in/out transitions
            img_clip = fadein(img_clip, 0.5)
            img_clip = fadeout(img_clip, 0.5)

            return img_clip

        except Exception as e:
            logger.error(f"Error creating scene from {image_path}: {e}")
            # Return black clip as fallback
            return ColorClip(
                size=(self.width, self.height),
                color=(0, 0, 0),
                duration=duration,
            )

    async def create_video(
        self,
        scenes: List[VideoScene],
        audio_path: Path,
        output_path: Path,
        title: str,
        add_intro: bool = True,
        add_outro: bool = True,
        bgm_path: Optional[Path] = None,
    ) -> Path:
        """Create complete video from scenes and audio.

        Args:
            scenes: List of video scenes
            audio_path: Path to audio narration
            output_path: Output video file path
            title: Video title
            add_intro: Whether to add intro
            add_outro: Whether to add outro
            bgm_path: Optional background music path

        Returns:
            Path to output video file
        """
        logger.info(f"Creating video with {len(scenes)} scenes")

        try:
            clips = []

            # Add intro
            if add_intro:
                intro = await self.create_intro(title, duration=3.0)
                clips.append(intro)

            # Add main content scenes
            for scene in scenes:
                scene_clip = await self.create_scene_from_image(
                    scene.image_path,
                    scene.duration,
                    scene.text_overlay,
                )
                clips.append(scene_clip)

            # Add outro
            if add_outro:
                outro = await self.create_outro(duration=5.0)
                clips.append(outro)

            # Concatenate all clips
            final_video = concatenate_videoclips(clips, method="compose")

            # Add audio narration
            if audio_path and audio_path.exists():
                audio = AudioFileClip(str(audio_path))
                final_video = final_video.set_audio(audio)

            # Add background music (optional, mixed with narration)
            if bgm_path and bgm_path.exists():
                try:
                    bgm = AudioFileClip(str(bgm_path))
                    # Loop BGM if shorter than video
                    if bgm.duration < final_video.duration:
                        bgm = bgm.audio_loop(duration=final_video.duration)
                    # Reduce BGM volume to not overpower narration
                    bgm = bgm.volumex(0.2)
                    # Mix with existing audio
                    if final_video.audio:
                        from moviepy.audio.AudioClip import CompositeAudioClip
                        final_audio = CompositeAudioClip([final_video.audio, bgm])
                        final_video = final_video.set_audio(final_audio)
                    else:
                        final_video = final_video.set_audio(bgm)
                except Exception as e:
                    logger.warning(f"Failed to add BGM: {e}")

            # Ensure output directory exists
            ensure_directory(output_path.parent)

            # Write video file
            logger.info(f"Writing video to {output_path}")
            final_video.write_videofile(
                str(output_path),
                fps=self.fps,
                codec="libx264",
                audio_codec="aac",
                audio_bitrate=settings.audio_bitrate,
                bitrate=settings.video_bitrate,
                preset="medium",
                threads=4,
            )

            # Clean up
            final_video.close()
            for clip in clips:
                clip.close()

            logger.info(f"Video created successfully: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error creating video: {e}")
            raise

    async def create_simple_video(
        self,
        images: List[Path],
        audio_path: Path,
        output_path: Path,
        title: str,
    ) -> Path:
        """Create simple video by distributing audio duration across images.

        Args:
            images: List of image paths
            audio_path: Path to audio file
            output_path: Output video path
            title: Video title

        Returns:
            Path to output video
        """
        # Get audio duration
        audio = AudioFileClip(str(audio_path))
        total_duration = audio.duration
        audio.close()

        # Calculate duration per image (excluding intro/outro)
        content_duration = total_duration - 8.0  # 3s intro + 5s outro
        if content_duration < 0:
            content_duration = total_duration

        scene_duration = content_duration / len(images) if images else 5.0

        # Create scenes
        scenes = [
            VideoScene(
                image_path=img,
                duration=scene_duration,
            )
            for img in images
        ]

        return await self.create_video(
            scenes=scenes,
            audio_path=audio_path,
            output_path=output_path,
            title=title,
        )
