"""Visual assets collection and generation module."""

import random
from pathlib import Path
from typing import List, Optional
from io import BytesIO

import requests
from PIL import Image

from src.core.config import get_settings
from src.core.logging import get_logger
from src.utils.helpers import sanitize_filename, ensure_directory

logger = get_logger(__name__)
settings = get_settings()


class VisualAssetsCollector:
    """Collect and generate visual assets for videos."""

    def __init__(self) -> None:
        """Initialize visual assets collector."""
        self.unsplash_api_key = None  # Optional
        self.pexels_api_key = None  # Optional

    async def search_unsplash(
        self,
        query: str,
        count: int = 5,
    ) -> List[Path]:
        """Search and download images from Unsplash.

        Args:
            query: Search query
            count: Number of images to download

        Returns:
            List of downloaded image paths
        """
        if not self.unsplash_api_key:
            logger.warning("Unsplash API key not configured, using fallback")
            return await self._get_fallback_images(count)

        try:
            url = "https://api.unsplash.com/search/photos"
            headers = {"Authorization": f"Client-ID {self.unsplash_api_key}"}
            params = {
                "query": query,
                "per_page": count,
                "orientation": "landscape",
            }

            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            images = []
            for idx, result in enumerate(data.get("results", [])[:count]):
                image_url = result["urls"]["regular"]
                image_path = await self._download_image(
                    image_url,
                    f"{sanitize_filename(query)}_{idx}.jpg",
                )
                if image_path:
                    images.append(image_path)

            logger.info(f"Downloaded {len(images)} images from Unsplash")
            return images

        except Exception as e:
            logger.error(f"Error searching Unsplash: {e}")
            return await self._get_fallback_images(count)

    async def search_pexels(
        self,
        query: str,
        count: int = 5,
    ) -> List[Path]:
        """Search and download images from Pexels.

        Args:
            query: Search query
            count: Number of images to download

        Returns:
            List of downloaded image paths
        """
        if not self.pexels_api_key:
            logger.warning("Pexels API key not configured, using fallback")
            return await self._get_fallback_images(count)

        try:
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": self.pexels_api_key}
            params = {
                "query": query,
                "per_page": count,
                "orientation": "landscape",
            }

            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            images = []
            for idx, photo in enumerate(data.get("photos", [])[:count]):
                image_url = photo["src"]["large"]
                image_path = await self._download_image(
                    image_url,
                    f"{sanitize_filename(query)}_{idx}.jpg",
                )
                if image_path:
                    images.append(image_path)

            logger.info(f"Downloaded {len(images)} images from Pexels")
            return images

        except Exception as e:
            logger.error(f"Error searching Pexels: {e}")
            return await self._get_fallback_images(count)

    async def _download_image(
        self,
        url: str,
        filename: str,
    ) -> Optional[Path]:
        """Download image from URL.

        Args:
            url: Image URL
            filename: Output filename

        Returns:
            Path to downloaded image or None
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Load and process image
            img = Image.open(BytesIO(response.content))

            # Convert to RGB if necessary
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Resize if too large
            max_size = (1920, 1080)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Save image
            output_path = settings.image_output_path / filename
            ensure_directory(output_path.parent)
            img.save(output_path, "JPEG", quality=90)

            logger.info(f"Downloaded image: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return None

    async def _get_fallback_images(self, count: int = 5) -> List[Path]:
        """Generate fallback placeholder images.

        Args:
            count: Number of images to generate

        Returns:
            List of generated image paths
        """
        images = []

        for i in range(count):
            # Generate gradient placeholder
            img = Image.new("RGB", (1920, 1080))
            pixels = img.load()

            # Create gradient
            color_start = random.randint(50, 150)
            color_end = random.randint(100, 200)

            for y in range(1080):
                r = int(color_start + (color_end - color_start) * y / 1080)
                g = int(color_start + (color_end - color_start) * y / 1080)
                b = int(color_start + (color_end - color_start) * y / 1080)
                for x in range(1920):
                    pixels[x, y] = (r, g, b)

            # Save placeholder
            filename = f"placeholder_{i}.jpg"
            output_path = settings.image_output_path / filename
            ensure_directory(output_path.parent)
            img.save(output_path, "JPEG")
            images.append(output_path)

        logger.info(f"Generated {len(images)} fallback images")
        return images

    async def collect_images_for_topic(
        self,
        topic: str,
        keywords: List[str],
        count: int = 5,
    ) -> List[Path]:
        """Collect images for a topic.

        Args:
            topic: Main topic
            keywords: Related keywords
            count: Number of images to collect

        Returns:
            List of image paths
        """
        # Try Unsplash first
        images = await self.search_unsplash(topic, count)

        # If not enough images, try keywords
        if len(images) < count and keywords:
            for keyword in keywords[:3]:
                additional = await self.search_unsplash(keyword, count - len(images))
                images.extend(additional)
                if len(images) >= count:
                    break

        # Fill remaining with fallback if needed
        if len(images) < count:
            fallback = await self._get_fallback_images(count - len(images))
            images.extend(fallback)

        return images[:count]

    async def create_title_card(
        self,
        title: str,
        output_path: Path,
        background_color: tuple = (30, 30, 60),
    ) -> Path:
        """Create title card image.

        Args:
            title: Title text
            output_path: Output image path
            background_color: Background RGB color

        Returns:
            Path to created image
        """
        from PIL import ImageDraw, ImageFont

        # Create image
        img = Image.new("RGB", (1920, 1080), background_color)
        draw = ImageDraw.Draw(img)

        # Try to load font, fallback to default if not available
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        except Exception:
            font = ImageFont.load_default()
            logger.warning("Using default font for title card")

        # Calculate text size and position
        bbox = draw.textbbox((0, 0), title, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (1920 - text_width) // 2
        y = (1080 - text_height) // 2

        # Draw text with shadow
        shadow_offset = 3
        draw.text((x + shadow_offset, y + shadow_offset), title, font=font, fill=(0, 0, 0))
        draw.text((x, y), title, font=font, fill=(255, 255, 255))

        # Save image
        ensure_directory(output_path.parent)
        img.save(output_path, "JPEG", quality=95)

        logger.info(f"Created title card: {output_path}")
        return output_path
