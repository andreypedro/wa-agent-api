"""
Generic Audio Transcription Service using Groq's Whisper API.

This service provides a reusable interface for transcribing audio files
that can be used by both Telegram and WhatsApp bots.
"""

import os
import tempfile
import logging
from typing import Optional, Tuple
from pathlib import Path

from groq import Groq

# Try to import pydub for audio conversion, but make it optional
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None

logger = logging.getLogger(__name__)


class AudioTranscriptionError(Exception):
    """Custom exception for audio transcription errors."""
    pass


class AudioTranscriptionService:
    """
    Generic service for transcribing audio files using Groq's Whisper API.
    
    This service handles:
    - Audio file processing
    - Format conversion (if needed)
    - Groq API communication
    - Error handling and cleanup
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the transcription service.
        
        Args:
            api_key: Groq API key. If not provided, will use GROQ_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key is required. Set GROQ_API_KEY environment variable.")
        
        self.client = Groq(api_key=self.api_key)
        
        # Supported audio formats by Groq
        self.supported_formats = {
            'flac', 'mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'ogg', 'wav', 'webm'
        }

        # Recommended model for fast transcription
        self.model = "whisper-large-v3-turbo"

        # Check if audio conversion is available
        self.conversion_available = PYDUB_AVAILABLE
    
    def _convert_audio_format(self, input_path: str, output_format: str = "wav") -> str:
        """
        Convert audio file to a supported format.

        Args:
            input_path: Path to input audio file
            output_format: Target format (default: "wav")

        Returns:
            Path to converted audio file

        Raises:
            AudioTranscriptionError: If conversion fails
        """
        if not self.conversion_available:
            raise AudioTranscriptionError("Audio conversion not available. Please install pydub and its dependencies.")

        try:
            logger.info(f"Converting audio from {input_path} to {output_format}")

            # Load audio file
            audio = AudioSegment.from_file(input_path)

            # Create temporary file for converted audio
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f".{output_format}",
                prefix="converted_audio_"
            ) as temp_file:
                output_path = temp_file.name

            # Export to target format
            audio.export(output_path, format=output_format)

            logger.info(f"Audio converted successfully to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Audio conversion failed: {str(e)}")
            raise AudioTranscriptionError(f"Failed to convert audio format: {str(e)}")

    def transcribe_audio(
        self,
        audio_file_path: str,
        language: str = "pt",
        prompt: Optional[str] = None
    ) -> str:
        """
        Transcribe an audio file to text.
        
        Args:
            audio_file_path: Path to the audio file
            language: Language code (default: "pt" for Portuguese)
            prompt: Optional prompt to guide transcription style
            
        Returns:
            Transcribed text
            
        Raises:
            AudioTranscriptionError: If transcription fails
        """
        converted_file_path = None
        try:
            # Validate file exists
            if not os.path.exists(audio_file_path):
                raise AudioTranscriptionError(f"Audio file not found: {audio_file_path}")

            # Check file size (Groq has limits)
            file_size = os.path.getsize(audio_file_path)
            max_size = 25 * 1024 * 1024  # 25MB for free tier
            if file_size > max_size:
                raise AudioTranscriptionError(f"Audio file too large: {file_size} bytes (max: {max_size})")

            # Check if format is supported
            file_extension = Path(audio_file_path).suffix.lower().lstrip('.')

            if file_extension not in self.supported_formats:
                # For now, since OGG is actually supported by Groq, let's try it directly
                # If it fails, we'll get a proper error from the API
                logger.warning(f"File extension '{file_extension}' not in known supported formats, but trying anyway")
                # Note: Groq actually supports OGG files directly, so this should work

            logger.info(f"Transcribing audio file: {audio_file_path} (size: {file_size} bytes)")
            
            # Prepare transcription parameters
            transcription_params = {
                "model": self.model,
                "language": language,
                "temperature": 0.0,  # For consistent results
                "response_format": "text"  # Simple text response
            }
            
            # Add prompt if provided
            if prompt:
                transcription_params["prompt"] = prompt[:224]  # Groq limit is 224 tokens
            
            # Perform transcription
            with open(audio_file_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    file=(os.path.basename(audio_file_path), audio_file.read()),
                    **transcription_params
                )
            
            # Extract text from response
            if hasattr(transcription, 'text'):
                transcribed_text = transcription.text.strip()
            else:
                transcribed_text = str(transcription).strip()
            
            if not transcribed_text:
                raise AudioTranscriptionError("Transcription returned empty text")
            
            logger.info(f"Transcription successful: {len(transcribed_text)} characters")
            return transcribed_text

        except Exception as e:
            if isinstance(e, AudioTranscriptionError):
                raise

            logger.error(f"Transcription failed: {str(e)}")
            raise AudioTranscriptionError(f"Failed to transcribe audio: {str(e)}")

        finally:
            # Clean up converted file if it was created
            if converted_file_path and os.path.exists(converted_file_path):
                try:
                    os.unlink(converted_file_path)
                    logger.debug(f"Cleaned up converted file: {converted_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete converted file {converted_file_path}: {e}")
    
    def transcribe_audio_from_bytes(
        self, 
        audio_bytes: bytes, 
        filename: str,
        language: str = "pt",
        prompt: Optional[str] = None
    ) -> str:
        """
        Transcribe audio from bytes data.
        
        Args:
            audio_bytes: Audio file content as bytes
            filename: Original filename (for format detection)
            language: Language code (default: "pt" for Portuguese)
            prompt: Optional prompt to guide transcription style
            
        Returns:
            Transcribed text
            
        Raises:
            AudioTranscriptionError: If transcription fails
        """
        temp_file_path = None
        try:
            # Create temporary file
            file_extension = Path(filename).suffix
            with tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=file_extension,
                prefix="audio_transcription_"
            ) as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            # Transcribe the temporary file
            return self.transcribe_audio(temp_file_path, language, prompt)
            
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file_path}: {e}")
    
    def get_supported_formats(self) -> set:
        """Get the set of supported audio formats."""
        return self.supported_formats.copy()
    
    def is_format_supported(self, filename: str) -> bool:
        """Check if the audio format is supported."""
        file_extension = Path(filename).suffix.lower().lstrip('.')
        return file_extension in self.supported_formats


# Global instance for easy access
_transcription_service = None


def get_transcription_service() -> AudioTranscriptionService:
    """Get a singleton instance of the transcription service."""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = AudioTranscriptionService()
    return _transcription_service
