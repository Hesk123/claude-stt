"""Tests for the WhisperAPIEngine."""

import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from claude_stt.engines.whisper_api import WhisperAPIEngine, _openai_available


class WhisperAPIEngineTests(unittest.TestCase):
    def test_not_available_without_api_key(self):
        """Engine should not be available without API key."""
        with patch.dict("os.environ", {}, clear=True):
            engine = WhisperAPIEngine(api_key=None)
            # If openai package is installed but no key, should be unavailable
            if _openai_available:
                self.assertFalse(engine.is_available())

    def test_available_with_api_key(self):
        """Engine should be available with API key (if openai installed)."""
        engine = WhisperAPIEngine(api_key="test-key")
        # Only available if openai package is installed
        if _openai_available:
            self.assertTrue(engine.is_available())
        else:
            self.assertFalse(engine.is_available())

    def test_api_key_from_env(self):
        """Engine should pick up API key from environment."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-test-key"}):
            engine = WhisperAPIEngine()
            self.assertEqual(engine.api_key, "env-test-key")

    def test_explicit_api_key_overrides_env(self):
        """Explicit API key should override environment variable."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}):
            engine = WhisperAPIEngine(api_key="explicit-key")
            self.assertEqual(engine.api_key, "explicit-key")

    def test_language_setting(self):
        """Language setting should be stored correctly."""
        engine = WhisperAPIEngine(api_key="test", language="en")
        self.assertEqual(engine.language, "en")

        engine2 = WhisperAPIEngine(api_key="test")
        self.assertIsNone(engine2.language)

    @patch("claude_stt.engines.whisper_api._OpenAI")
    @patch("claude_stt.engines.whisper_api._openai_available", True)
    def test_transcribe_creates_wav(self, mock_openai_class):
        """Transcribe should convert audio to WAV format for API."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.audio.transcriptions.create.return_value = MagicMock(text="Hello world")

        engine = WhisperAPIEngine(api_key="test-key")

        # Create test audio
        audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence

        result = engine.transcribe(audio, sample_rate=16000)

        self.assertEqual(result, "Hello world")
        mock_client.audio.transcriptions.create.assert_called_once()

        # Check that file parameter was passed
        call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
        self.assertEqual(call_kwargs["model"], "whisper-1")
        self.assertIn("file", call_kwargs)

    @patch("claude_stt.engines.whisper_api._OpenAI")
    @patch("claude_stt.engines.whisper_api._openai_available", True)
    def test_transcribe_with_language(self, mock_openai_class):
        """Transcribe should pass language parameter to API."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.audio.transcriptions.create.return_value = MagicMock(text="Hola mundo")

        engine = WhisperAPIEngine(api_key="test-key", language="es")
        audio = np.zeros(16000, dtype=np.float32)

        result = engine.transcribe(audio, sample_rate=16000)

        call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
        self.assertEqual(call_kwargs["language"], "es")

    def test_transcribe_returns_empty_when_unavailable(self):
        """Transcribe should return empty string when engine unavailable."""
        with patch.dict("os.environ", {}, clear=True):
            engine = WhisperAPIEngine(api_key=None)
            audio = np.zeros(16000, dtype=np.float32)

            result = engine.transcribe(audio, sample_rate=16000)

            self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
