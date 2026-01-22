import unittest

from claude_stt.config import Config


class ConfigTests(unittest.TestCase):
    def test_config_validation_clamps_invalid_values(self):
        config = Config(
            mode="bad",
            engine="nope",
            output_mode="wat",
            moonshine_model="moonshine/huge",
            max_recording_seconds=0,
            sample_rate=8000,
        ).validate()

        self.assertEqual(config.mode, "toggle")
        self.assertEqual(config.engine, "moonshine")
        self.assertEqual(config.output_mode, "auto")
        self.assertEqual(config.moonshine_model, "moonshine/base")
        self.assertEqual(config.max_recording_seconds, 1)
        self.assertEqual(config.sample_rate, 16000)

    def test_whisper_api_engine_valid(self):
        config = Config(engine="whisper-api").validate()
        self.assertEqual(config.engine, "whisper-api")

    def test_whisper_api_language_default(self):
        config = Config(engine="whisper-api").validate()
        self.assertEqual(config.whisper_api_language, "")

    def test_all_valid_engines(self):
        for engine in ["moonshine", "whisper", "whisper-api"]:
            config = Config(engine=engine).validate()
            self.assertEqual(config.engine, engine)


if __name__ == "__main__":
    unittest.main()
