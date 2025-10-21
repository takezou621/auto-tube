"""Thumbnail generation module for YouTube videos."""

from pathlib import Path
from typing import Optional, Tuple
import random

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

from src.core.config import get_settings
from src.core.logging import get_logger
from src.utils.helpers import ensure_directory

logger = get_logger(__name__)
settings = get_settings()


class ThumbnailGenerator:
    """Generate eye-catching thumbnails for YouTube videos."""

    def __init__(self) -> None:
        """Initialize thumbnail generator."""
        self.width = 1280
        self.height = 720
        self.templates = ["bold", "minimal", "colorful", "tech"]

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Get font with fallback.

        Args:
            size: Font size

        Returns:
            Font object
        """
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]

        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue

        logger.warning("No TrueType font found, using default")
        return ImageFont.load_default()

    def _wrap_text(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int,
    ) -> list[str]:
        """Wrap text to fit within max width.

        Args:
            text: Input text
            font: Font to use
            max_width: Maximum width in pixels

        Returns:
            List of text lines
        """
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = font.getbbox(test_line)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _create_gradient_background(
        self,
        color_start: Tuple[int, int, int],
        color_end: Tuple[int, int, int],
    ) -> Image.Image:
        """Create gradient background.

        Args:
            color_start: Start RGB color
            color_end: End RGB color

        Returns:
            Image with gradient
        """
        img = Image.new("RGB", (self.width, self.height))
        draw = ImageDraw.Draw(img)

        for y in range(self.height):
            r = int(color_start[0] + (color_end[0] - color_start[0]) * y / self.height)
            g = int(color_start[1] + (color_end[1] - color_start[1]) * y / self.height)
            b = int(color_start[2] + (color_end[2] - color_start[2]) * y / self.height)

            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

        return img

    async def generate_bold_template(
        self,
        text: str,
        background_image: Optional[Path] = None,
    ) -> Image.Image:
        """Generate bold, high-contrast thumbnail.

        Args:
            text: Thumbnail text
            background_image: Optional background image

        Returns:
            Thumbnail image
        """
        # Create or load background
        if background_image and background_image.exists():
            img = Image.open(background_image)
            img = img.resize((self.width, self.height))
            # Darken background
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.4)
            # Add blur
            img = img.filter(ImageFilter.GaussianBlur(radius=3))
        else:
            # Create gradient background
            img = self._create_gradient_background((255, 50, 50), (100, 20, 100))

        draw = ImageDraw.Draw(img)

        # Add text
        font = self._get_font(90)
        max_width = self.width - 100

        lines = self._wrap_text(text, font, max_width)

        # Calculate total text height
        total_height = sum([font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines])
        total_height += (len(lines) - 1) * 20  # Line spacing

        y = (self.height - total_height) // 2

        for line in lines:
            bbox = font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (self.width - text_width) // 2

            # Draw text shadow
            shadow_offset = 5
            draw.text((x + shadow_offset, y + shadow_offset), line, font=font, fill=(0, 0, 0))

            # Draw main text
            draw.text((x, y), line, font=font, fill=(255, 255, 255))

            y += text_height + 20

        return img

    async def generate_minimal_template(
        self,
        text: str,
        background_image: Optional[Path] = None,
    ) -> Image.Image:
        """Generate minimal, clean thumbnail.

        Args:
            text: Thumbnail text
            background_image: Optional background image

        Returns:
            Thumbnail image
        """
        # Create background
        if background_image and background_image.exists():
            img = Image.open(background_image)
            img = img.resize((self.width, self.height))
        else:
            img = Image.new("RGB", (self.width, self.height), (245, 245, 250))

        draw = ImageDraw.Draw(img)

        # Add semi-transparent overlay
        overlay = Image.new("RGBA", (self.width, self.height), (255, 255, 255, 200))
        img.paste(overlay, (0, 0), overlay)

        # Add text
        font = self._get_font(70)
        max_width = self.width - 200

        lines = self._wrap_text(text, font, max_width)

        # Calculate position
        total_height = sum([font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines])
        total_height += (len(lines) - 1) * 15

        y = (self.height - total_height) // 2

        for line in lines:
            bbox = font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (self.width - text_width) // 2

            # Draw text
            draw.text((x, y), line, font=font, fill=(30, 30, 40))

            y += text_height + 15

        return img

    async def generate_colorful_template(
        self,
        text: str,
        background_image: Optional[Path] = None,
    ) -> Image.Image:
        """Generate colorful, vibrant thumbnail.

        Args:
            text: Thumbnail text
            background_image: Optional background image

        Returns:
            Thumbnail image
        """
        # Random vibrant colors
        colors = [
            ((255, 107, 107), (255, 178, 55)),  # Red to Orange
            ((72, 219, 251), (29, 151, 248)),   # Cyan to Blue
            ((255, 94, 218), (194, 54, 255)),   # Pink to Purple
            ((72, 219, 132), (29, 209, 161)),   # Green to Teal
        ]

        color_pair = random.choice(colors)
        img = self._create_gradient_background(color_pair[0], color_pair[1])

        draw = ImageDraw.Draw(img)

        # Add decorative elements
        for _ in range(10):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(50, 150)
            alpha = random.randint(30, 80)
            color = (255, 255, 255, alpha)

            circle_img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            circle_draw = ImageDraw.Draw(circle_img)
            circle_draw.ellipse([x, y, x + size, y + size], fill=color)
            circle_img = circle_img.filter(ImageFilter.GaussianBlur(radius=20))
            img.paste(circle_img, (0, 0), circle_img)

        # Add text
        font = self._get_font(85)
        max_width = self.width - 150

        lines = self._wrap_text(text, font, max_width)

        total_height = sum([font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines])
        total_height += (len(lines) - 1) * 18

        y = (self.height - total_height) // 2

        for line in lines:
            bbox = font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (self.width - text_width) // 2

            # Draw text with strong shadow
            for offset in range(6, 0, -1):
                alpha = int(255 * (1 - offset / 6))
                shadow_color = (0, 0, 0, alpha)
                shadow_img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow_img)
                shadow_draw.text((x + offset, y + offset), line, font=font, fill=shadow_color)
                img.paste(shadow_img, (0, 0), shadow_img)

            # Draw main text
            text_img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_img)
            text_draw.text((x, y), line, font=font, fill=(255, 255, 255))
            img.paste(text_img, (0, 0), text_img)

            y += text_height + 18

        return img

    async def generate_tech_template(
        self,
        text: str,
        background_image: Optional[Path] = None,
    ) -> Image.Image:
        """Generate tech-themed thumbnail.

        Args:
            text: Thumbnail text
            background_image: Optional background image

        Returns:
            Thumbnail image
        """
        # Tech color scheme
        img = self._create_gradient_background((20, 30, 48), (44, 62, 80))

        draw = ImageDraw.Draw(img)

        # Add circuit-like lines
        for _ in range(15):
            x1 = random.randint(0, self.width)
            y1 = random.randint(0, self.height)
            x2 = random.randint(0, self.width)
            y2 = random.randint(0, self.height)
            draw.line([(x1, y1), (x2, y2)], fill=(100, 150, 200, 30), width=2)

        # Add text
        font = self._get_font(80)
        max_width = self.width - 120

        lines = self._wrap_text(text, font, max_width)

        total_height = sum([font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines])
        total_height += (len(lines) - 1) * 16

        y = (self.height - total_height) // 2

        for line in lines:
            bbox = font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (self.width - text_width) // 2

            # Draw neon glow effect
            for i in range(5, 0, -1):
                glow_color = (52, 152, 219, int(255 * (1 - i / 5)))
                glow_img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
                glow_draw = ImageDraw.Draw(glow_img)
                glow_draw.text((x, y), line, font=font, fill=glow_color)
                glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=i * 2))
                img.paste(glow_img, (0, 0), glow_img)

            # Draw main text
            text_img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_img)
            text_draw.text((x, y), line, font=font, fill=(255, 255, 255))
            img.paste(text_img, (0, 0), text_img)

            y += text_height + 16

        return img

    async def generate_thumbnail(
        self,
        text: str,
        output_path: Path,
        template: str = "bold",
        background_image: Optional[Path] = None,
    ) -> Path:
        """Generate thumbnail with specified template.

        Args:
            text: Thumbnail text
            output_path: Output file path
            template: Template name (bold, minimal, colorful, tech)
            background_image: Optional background image

        Returns:
            Path to generated thumbnail
        """
        logger.info(f"Generating thumbnail with template: {template}")

        try:
            # Generate based on template
            if template == "bold":
                img = await self.generate_bold_template(text, background_image)
            elif template == "minimal":
                img = await self.generate_minimal_template(text, background_image)
            elif template == "colorful":
                img = await self.generate_colorful_template(text, background_image)
            elif template == "tech":
                img = await self.generate_tech_template(text, background_image)
            else:
                logger.warning(f"Unknown template: {template}, using bold")
                img = await self.generate_bold_template(text, background_image)

            # Ensure output directory exists
            ensure_directory(output_path.parent)

            # Convert to RGB if needed
            if img.mode == "RGBA":
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img

            # Save thumbnail
            img.save(output_path, "JPEG", quality=95, optimize=True)

            logger.info(f"Thumbnail generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            raise

    async def generate_multiple_variants(
        self,
        text: str,
        output_dir: Path,
        background_image: Optional[Path] = None,
    ) -> list[Path]:
        """Generate multiple thumbnail variants for A/B testing.

        Args:
            text: Thumbnail text
            output_dir: Output directory
            background_image: Optional background image

        Returns:
            List of generated thumbnail paths
        """
        ensure_directory(output_dir)
        thumbnails = []

        for template in self.templates:
            output_path = output_dir / f"thumbnail_{template}.jpg"
            thumbnail = await self.generate_thumbnail(
                text, output_path, template, background_image
            )
            thumbnails.append(thumbnail)

        logger.info(f"Generated {len(thumbnails)} thumbnail variants")
        return thumbnails
