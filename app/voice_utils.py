from __future__ import annotations

import base64
import io
from typing import Optional, Tuple

from openai import OpenAI

from app.config import settings


class VoiceProcessor:
    """Handles speech-to-text and text-to-speech operations using OpenAI APIs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ) -> None:
        """
        Initialize voice processor.
        
        Args:
            api_key: OpenAI API key (defaults to settings.llm_api_key)
            api_base: Optional API base URL override
        """
        self.api_key = api_key or settings.llm_api_key
        self.api_base = api_base or settings.llm_api_base
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required for voice processing")
        
        # Initialize OpenAI client
        client_kwargs = {"api_key": self.api_key}
        if self.api_base:
            client_kwargs["base_url"] = self.api_base
        self.client = OpenAI(**client_kwargs)

    def speech_to_text(
        self,
        audio_bytes: bytes,
        audio_format: str = "webm",
    ) -> Tuple[str, str]:
        """
        Convert speech to text using OpenAI Whisper API.
        
        Args:
            audio_bytes: Audio file content as bytes
            audio_format: Audio format (webm, mp3, wav, etc.)
            
        Returns:
            Tuple of (transcribed_text, detected_language_code)
            Language code: "ar" for Arabic, "en" for English, or other ISO codes
        """
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
        
        # Determine MIME type based on format
        mime_type_map = {
            "webm": "audio/webm",
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "m4a": "audio/m4a",
            "ogg": "audio/ogg",
        }
        mime_type = mime_type_map.get(audio_format.lower(), "audio/webm")
        
        # Create a file-like object from bytes
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = f"audio.{audio_format}"
        
        try:
            # Call Whisper API with verbose_json to get language info
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",  # Get language info
            )
            
            # Extract text and language
            # The response format depends on the API version
            if hasattr(transcript, 'text'):
                text = transcript.text
            else:
                # Fallback if response format is different
                text = str(transcript)
            
            # Extract language code
            language_code = "en"  # Default
            if hasattr(transcript, 'language'):
                language_code = transcript.language
            elif isinstance(transcript, dict):
                language_code = transcript.get("language", "en")
            
            # Normalize language code to "ar" or "en" for our use case
            if language_code in ["ar", "arabic"]:
                language_code = "ar"
            elif language_code in ["en", "english"]:
                language_code = "en"
            else:
                # Try to detect from text content if language code not available
                # Check if text contains Arabic characters
                import re
                arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
                if arabic_pattern.search(text):
                    language_code = "ar"
                else:
                    language_code = "en"
            
            return text, language_code
            
        except Exception as e:
            raise RuntimeError(f"Speech-to-text conversion failed: {str(e)}") from e

    def text_to_speech(
        self,
        text: str,
        language: str = "en",
        voice: str = "alloy",
        model: str = "tts-1",
    ) -> bytes:
        """
        Convert text to speech using OpenAI TTS API.
        
        Args:
            text: Text to convert to speech
            language: Language code ("ar" for Arabic, "en" for English)
            voice: Voice to use. Options: "alloy", "echo", "fable", "onyx", "nova", "shimmer"
                   For Arabic, "nova" or "alloy" work well
            model: TTS model ("tts-1" or "tts-1-hd")
            
        Returns:
            Audio bytes in MP3 format
        """
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
        
        # For Arabic text, we can use any voice but ensure the model supports it
        # OpenAI TTS supports Arabic, but we may need to adjust voice selection
        # Note: OpenAI TTS doesn't have language-specific voices, but handles Arabic well
        
        try:
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
            )
            
            # Read the audio bytes
            audio_bytes = b""
            for chunk in response.iter_bytes():
                audio_bytes += chunk
            
            return audio_bytes
            
        except Exception as e:
            raise RuntimeError(f"Text-to-speech conversion failed: {str(e)}") from e

    def validate_audio_format(self, content_type: Optional[str], filename: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validate audio file format.
        
        Args:
            content_type: MIME type of the file
            filename: Optional filename for format detection
            
        Returns:
            Tuple of (is_valid, format_string)
        """
        # Supported formats
        supported_types = [
            "audio/webm",
            "audio/mpeg",
            "audio/mp3",
            "audio/wav",
            "audio/x-wav",
            "audio/m4a",
            "audio/ogg",
        ]
        
        # Check content type
        if content_type and any(supported in content_type.lower() for supported in supported_types):
            # Extract format from content type
            if "webm" in content_type.lower():
                return True, "webm"
            elif "mpeg" in content_type.lower() or "mp3" in content_type.lower():
                return True, "mp3"
            elif "wav" in content_type.lower():
                return True, "wav"
            elif "m4a" in content_type.lower():
                return True, "m4a"
            elif "ogg" in content_type.lower():
                return True, "ogg"
        
        # Fallback: check filename extension
        if filename:
            ext = filename.lower().split(".")[-1] if "." in filename else ""
            if ext in ["webm", "mp3", "wav", "m4a", "ogg"]:
                return True, ext
        
        return False, "unknown"

    def validate_audio_size(self, audio_bytes: bytes, max_size_mb: int = 25) -> bool:
        """
        Validate audio file size.
        
        Args:
            audio_bytes: Audio file content as bytes
            max_size_mb: Maximum size in MB (default: 25MB, OpenAI Whisper limit)
            
        Returns:
            True if size is valid, False otherwise
        """
        size_mb = len(audio_bytes) / (1024 * 1024)
        return size_mb <= max_size_mb


# Global voice processor instance
_voice_processor: Optional[VoiceProcessor] = None


def get_voice_processor() -> VoiceProcessor:
    """Get or create global voice processor instance."""
    global _voice_processor
    if _voice_processor is None:
        _voice_processor = VoiceProcessor()
    return _voice_processor

