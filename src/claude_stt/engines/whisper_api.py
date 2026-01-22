"""OpenAI Whisper API engine for cloud-based speech-to-text."""

from __future__ import annotations

import io
import logging
import os
import wave
from typing import Optional

import numpy as np

_openai_available = False
_OpenAI = None

try:
    from openai import OpenAI as _OpenAI

    _openai_available = True
except ImportError:
    pass


class WhisperAPIEngine:
    """OpenAI Whisper API speech-to-text engine.

    Uses the OpenAI API for cloud-based transcription. Requires an API key
    set via OPENAI_API_KEY environment variable or passed directly.

    Models:
        - whisper-1: OpenAI's production Whisper model
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "whisper-1",
        language: Optional[str] = None,
    ):
        """Initialize the OpenAI Whisper API engine.

        Args:
            api_key: OpenAI API key. If not provided, uses OPENAI_API_KEY env var.
            model: Model to use (currently only "whisper-1" is available).
            language: Optional language code (e.g., "en", "es"). Auto-detected if not set.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.language = language
        self._client: Optional[object] = None
        self._logger = logging.getLogger(__name__)

    def is_available(self) -> bool:
        """Check if the OpenAI SDK is available and API key is set."""
        return _openai_available and bool(self.api_key)

    def load_model(self) -> bool:
        """Initialize the OpenAI client.

        Returns:
            True if client initialized successfully.
        """
        if not self.is_available():
            if not _openai_available:
                self._logger.warning("openai package not installed")
            elif not self.api_key:
                self._logger.warning("OPENAI_API_KEY not set")
            return False

        if self._client is not None:
            return True

        try:
            self._client = _OpenAI(api_key=self.api_key)
            return True
        except Exception:
            self._logger.exception("Failed to initialize OpenAI client")
            return False

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio using the OpenAI Whisper API.

        Args:
            audio: Audio data as numpy array (float32, mono).
            sample_rate: Sample rate of the audio.

        Returns:
            Transcribed text, or empty string if transcription fails.
        """
        if not self.load_model():
            return ""

        try:
            # Convert float32 audio to int16 WAV format for API
            if audio.dtype == np.float32:
                audio_int16 = (audio * 32767).astype(np.int16)
            else:
                audio_int16 = audio.astype(np.int16)

            # Create in-memory WAV file
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_int16.tobytes())

            wav_buffer.seek(0)
            wav_buffer.name = "audio.wav"

            # Call OpenAI API
            kwargs = {"model": self.model, "file": wav_buffer}
            if self.language:
                kwargs["language"] = self.language

            response = self._client.audio.transcriptions.create(**kwargs)
            return response.text.strip()

        except Exception:
            self._logger.exception("OpenAI Whisper API transcription failed")
            return ""
