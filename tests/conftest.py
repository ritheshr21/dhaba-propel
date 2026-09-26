import os

import pytest

# Default tests to offline fixture mode (no API key, no network).
os.environ.setdefault("DHABA_LLM_MODE", "replay")


@pytest.fixture(autouse=True)
def _reset_llm_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DHABA_LLM_MODE", "replay")
