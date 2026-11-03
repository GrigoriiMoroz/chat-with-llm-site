import os
os.environ.setdefault("HUGGING_FACE_API_KEY", "test-only-token")
import asyncio
import httpx
import pytest
import main
from fastapi.testclient import TestClient

@pytest.mark.parametrize("value", ["", "   ", "\n\t", "x"*4001, None, 12, [], {}])
def test_invalid_messages_never_reach_provider(monkeypatch, value):
    async def fail(message, *args): pytest.fail("Provider must not be called")
    monkeypatch.setattr(main,"call_llm",fail)
    assert TestClient(main.app).post("/chat",json={"message":value}).status_code == 422

@pytest.mark.parametrize("value", [" hi ", "я"*4000])
def test_valid_message_is_trimmed(monkeypatch, value):
    seen=[]
    async def fake(message, *args): seen.append(message); return "ok"
    monkeypatch.setattr(main,"call_llm",fake)
    r=TestClient(main.app).post("/chat",json={"message":value})
    assert r.status_code == 200
    assert seen == [value.strip()]
