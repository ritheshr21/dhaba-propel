import os
from enum import Enum
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIXTURES_DIR = PROJECT_ROOT / "fixtures" / "llm"


class LlmMode(str, Enum):
    REPLAY = "replay"
    LIVE = "live"


def get_llm_mode() -> LlmMode:
    raw = os.environ.get("DHABA_LLM_MODE", LlmMode.REPLAY.value).strip().lower()
    try:
        return LlmMode(raw)
    except ValueError as exc:
        raise ValueError(
            f"Invalid DHABA_LLM_MODE={raw!r}; use {LlmMode.REPLAY.value!r} or {LlmMode.LIVE.value!r}."
        ) from exc


def get_fixtures_dir() -> Path:
    override = os.environ.get("DHABA_FIXTURES_DIR")
    if override:
        return Path(override)
    return DEFAULT_FIXTURES_DIR


@lru_cache
def get_extraction_max_retries() -> int:
    raw = os.environ.get("DHABA_EXTRACTION_MAX_RETRIES", "2")
    return max(0, int(raw))
