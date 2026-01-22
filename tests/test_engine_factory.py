import unittest

from claude_stt.config import Config
from claude_stt.engine_factory import build_engine
from claude_stt.engines.moonshine import MoonshineEngine
from claude_stt.engines.whisper import WhisperEngine
from claude_stt.engines.whisper_api import WhisperAPIEngine
from claude_stt.errors import EngineError


class EngineFactoryTests(unittest.TestCase):
    def test_unknown_engine_rejected(self):
        config = Config(engine="unknown").validate()
        # validate defaults to moonshine, so force raw config
        config.engine = "unknown"
        with self.assertRaises(EngineError):
            build_engine(config)

    def test_moonshine_engine_constructed(self):
        config = Config(engine="moonshine")
        engine = build_engine(config)
        self.assertIsInstance(engine, MoonshineEngine)

    def test_whisper_engine_constructed(self):
        config = Config(engine="whisper")
        engine = build_engine(config)
        self.assertIsInstance(engine, WhisperEngine)

    def test_whisper_api_engine_constructed(self):
        config = Config(engine="whisper-api")
        engine = build_engine(config)
        self.assertIsInstance(engine, WhisperAPIEngine)

    def test_whisper_api_language_passed(self):
        config = Config(engine="whisper-api", whisper_api_language="en")
        engine = build_engine(config)
        self.assertIsInstance(engine, WhisperAPIEngine)
        self.assertEqual(engine.language, "en")

    def test_whisper_api_empty_language_becomes_none(self):
        config = Config(engine="whisper-api", whisper_api_language="")
        engine = build_engine(config)
        self.assertIsNone(engine.language)


if __name__ == "__main__":
    unittest.main()
