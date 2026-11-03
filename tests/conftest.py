import os

import pytest

os.environ.setdefault("HUGGING_FACE_API_KEY", "test-only-token")


@pytest.fixture(autouse=True)
def isolate_inference_limits(monkeypatch):
    """Каждый тест начинает с пустого лимитера и локального режима."""
    import main

    main.request_windows.clear()
    monkeypatch.setattr(main, "API_ACCESS_KEY", "")
    monkeypatch.setattr(main, "RATE_LIMIT_REQUESTS", 10000)
    yield
    main.request_windows.clear()
