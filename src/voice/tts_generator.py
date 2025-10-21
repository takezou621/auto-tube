"""Text-to-Speech generation module."""

from pathlib import Path
from typing import Optional

from elevenlabs import generate, save
from elevenlabs.client import ElevenLabs

from src.core.config import get_settings
from src.core.logging import get_logger
from src.utils.helpers import sanitize_filename

logger = get_logger(__name__)
settings = get_settings()


class TTSGenerator:
    """Generate speech from text using ElevenLabs or Google TTS."""

    def __init__(self) -> None:
        """Initialize TTS generator."""
        self.use_elevenlabs = bool(settings.elevenlabs_api_key)

        if self.use_elevenlabs:
            self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)
            self.voice_id = settings.elevenlabs_voice_id
            logger.info("TTS initialized with ElevenLabs")
        else:
            logger.warning("ElevenLabs API key not found, TTS will not work")

    async def generate_speech(
        self,
        text: str,
        output_path: Optional[Path] = None,
        voice_id: Optional[str] = None,
    ) -> Path:
        """Generate speech from text.

        Args:
            text: Text to convert to speech
            output_path: Output file path
            voice_id: Voice ID to use

        Returns:
            Path to generated audio file
        """
        if not self.use_elevenlabs:
            raise ValueError("TTS service not configured")

        try:
            # Set default output path if not provided
            if output_path is None:
                filename = sanitize_filename(text[:50]) + ".mp3"
                output_path = settings.audio_output_path / filename

            # Use provided voice_id or default
            voice = voice_id or self.voice_id

            logger.info(f"Generating speech for {len(text)} characters")

            # Generate audio using ElevenLabs
            audio = generate(
                text=text,
                voice=voice,
                model="eleven_multilingual_v2",
                api_key=settings.elevenlabs_api_key,
            )

            # Save audio to file
            save(audio, str(output_path))

            logger.info(f"Speech generated successfully: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            raise

    async def generate_speech_for_script(
        self,
        script: str,
        video_id: str,
    ) -> Path:
        """Generate speech for entire video script.

        Args:
            script: Complete video script
            video_id: Video identifier

        Returns:
            Path to generated audio file
        """
        output_path = settings.audio_output_path / f"{video_id}_narration.mp3"
        return await self.generate_speech(script, output_path)

    def estimate_speech_duration(self, text: str) -> int:
        """Estimate speech duration in seconds.

        Args:
            text: Input text

        Returns:
            Estimated duration in seconds
        """
        # Japanese speech: approximately 5-6 characters per second
        # This is a rough estimate
        chars_per_second = 5
        duration = len(text) // chars_per_second
        return duration
