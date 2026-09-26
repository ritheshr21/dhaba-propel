from app.config import get_fixtures_dir, get_llm_mode, LlmMode
from app.providers.base import ModelProvider
from app.providers.fixture import FixtureModelProvider
from app.providers.live import LiveModelProvider


def get_model_provider() -> ModelProvider:
    mode = get_llm_mode()
    if mode is LlmMode.REPLAY:
        return FixtureModelProvider(get_fixtures_dir())
    if mode is LlmMode.LIVE:
        return LiveModelProvider()
    raise ValueError(f"Unsupported LLM mode: {mode!r}")
