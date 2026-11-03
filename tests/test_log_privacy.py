import os
os.environ.setdefault("HUGGING_FACE_API_KEY", "test-only-token")
import asyncio
from concurrent.futures import ThreadPoolExecutor
import httpx
import pytest
import main
from fastapi.testclient import TestClient

def run_llm(message):
    # Playwright keeps an event loop in the main thread; isolate asyncio.run.
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, main.call_llm(message)).result()


@pytest.mark.parametrize("status", [200, 401, 403, 429, 500, 503])
def test_logs_do_not_contain_token_or_conversation(monkeypatch, caplog, status):
    secret = "PRIVATE-QUESTION-AND-ANSWER"
    original = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: httpx.Response(
        status, json={"choices": [{"message": {"content": secret}}], "error": secret}))
    monkeypatch.setattr(main.httpx, "AsyncClient", lambda **kw: original(transport=transport, **kw))
    caplog.set_level("INFO")
    try:
        run_llm(secret)
    except (ValueError, getattr(main, "LLMError", ValueError)):
        pass
    assert secret not in caplog.text
    assert main.HUGGING_FACE_API_KEY not in caplog.text
    assert "Authorization" not in caplog.text

def test_exception_details_are_not_logged(monkeypatch, caplog):
    original = httpx.AsyncClient
    def fail(request):
        raise RuntimeError("PRIVATE-EXCEPTION-CONTENT")
    monkeypatch.setattr(main.httpx, "AsyncClient", lambda **kw: original(transport=httpx.MockTransport(fail), **kw))
    with pytest.raises((ValueError, getattr(main, "LLMError", ValueError))):
        run_llm("private prompt")
    assert "PRIVATE-EXCEPTION-CONTENT" not in caplog.text
