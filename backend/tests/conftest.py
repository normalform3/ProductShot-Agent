from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def use_mock_text_provider():
    from app.config import settings

    original_provider = settings.text_provider
    settings.text_provider = "mock"
    try:
        yield
    finally:
        settings.text_provider = original_provider
