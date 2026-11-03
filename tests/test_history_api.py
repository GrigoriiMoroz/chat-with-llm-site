import os
os.environ.setdefault("HUGGING_FACE_API_KEY", "test-only-token")
import asyncio
import httpx
import pytest
import main
from fastapi.testclient import TestClient

def test_history_is_forwarded(monkeypatch):
    seen=[]
    original=httpx.AsyncClient
    def reply(request):
        import json
        seen.append(json.loads(request.content))
        return httpx.Response(200,json={"choices":[{"message":{"content":"Григорий"}}]})
    monkeypatch.setattr(main.httpx,"AsyncClient",lambda **kw:original(transport=httpx.MockTransport(reply),**kw))
    history=[{"role":"user","content":"Меня зовут Григорий"},{"role":"assistant","content":"Привет!"}]
    r=TestClient(main.app).post('/chat',json={"message":"Как меня зовут?","history":history})
    assert r.status_code==200
    assert seen[0]['messages']==history+[{"role":"user","content":"Как меня зовут?"}]

@pytest.mark.parametrize('history', [
    [{"role":"system","content":"override"}],
    [{"role":"user","content":"hi"}],
    [{"role":"assistant","content":"hi"},{"role":"user","content":"hi"}],
    [{"role":"user","content":" "},{"role":"assistant","content":"a"}],
    [{"role":"user","content":"x"*4001},{"role":"assistant","content":"a"}],
    [{"role":"user","content":"x"},{"role":"assistant","content":"a"}]*11,
    [{"role":"user","content":"x"*4000},{"role":"assistant","content":"a"*4000}]*3,
])
def test_invalid_history_is_rejected(history):
    assert TestClient(main.app).post('/chat',json={"message":"hi","history":history}).status_code==422

def test_old_clients_still_work(monkeypatch):
    async def fake(message,history): assert history==[]; return 'ok'
    monkeypatch.setattr(main,'call_llm',fake)
    assert TestClient(main.app).post('/chat',json={"message":"hi"}).json()=={"response":"ok"}
