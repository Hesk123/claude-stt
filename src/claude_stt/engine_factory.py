"""STT engine construction and validation."""

from .config import Config
from .engines import STTEngine
from .engines.moonshine import MoonshineEngine
from .engines.whisper import WhisperEngine
from .engines.whisper_api import WhisperAPIEngine
from .errors import EngineError


def build_engine(config: Config) -> STTEngine:
    """Create an engine instance for the configured engine."""
    if config.engine == "moonshine":
        return MoonshineEngine(model_name=config.moonshine_model)
    if config.engine == "whisper":
        return WhisperEngine(model_name=config.whisper_model)
    if config.engine == "whisper-api":
        language = config.whisper_api_language or None
        return WhisperAPIEngine(language=language)
    raise EngineError(f"Unknown engine '{config.engine}'")
