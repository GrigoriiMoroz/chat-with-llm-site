import os
os.environ.setdefault("HUGGING_FACE_API_KEY", "test-only-token")
import asyncio
import httpx
import pytest
import main
from fastapi.testclient import TestClient

@pytest.mark.parametrize("upstream,expected", [(401,502),(403,502),(429,429),(500,502),(503,503)])
def test_provider_errors(monkeypatch, upstream, expected):
    original = httpx.AsyncClient
    monkeypatch.setattr(main.httpx, "AsyncClient", lambda **kw: original(transport=httpx.MockTransport(
        lambda r: httpx.Response(upstream, text="PRIVATE-PROVIDER-DETAILS")), **kw))
    response = TestClient(main.app).post("/chat", json={"message": "hello"})
    assert response.status_code == expected
    assert "response" not in response.json()
    assert set(response.json()["detail"]) == {"code", "message"}
    assert "PRIVATE" not in response.text

@pytest.mark.parametrize("payload", [{}, {"choices": []}, {"choices":[{"message":{"content":None}}]}, {"choices":[{"message":{"content":" "}}]}])
def test_malformed_responses(monkeypatch, payload):
    original = httpx.AsyncClient
    monkeypatch.setattr(main.httpx, "AsyncClient", lambda **kw: original(transport=httpx.MockTransport(
        lambda r: httpx.Response(200, json=payload)), **kw))
    response = TestClient(main.app).post("/chat", json={"message":"hello"})
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "invalid_response"

@pytest.mark.parametrize("error,status", [(httpx.ReadTimeout("secret"),504),(httpx.ConnectError("secret"),502)])
def test_transport_failure(monkeypatch, error, status):
    original = httpx.AsyncClient
    def fail(r): raise error
    monkeypatch.setattr(main.httpx, "AsyncClient", lambda **kw: original(transport=httpx.MockTransport(fail), **kw))
    r = TestClient(main.app).post("/chat", json={"message":"hello"})
    assert r.status_code == status
    assert "secret" not in r.text

def test_success(monkeypatch):
    async def fake(message, *args): return "answer"
    monkeypatch.setattr(main, "call_llm", fake)
    assert TestClient(main.app).post("/chat",json={"message":"hi"}).json() == {"response":"answer"}
