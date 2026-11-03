import os
os.environ.setdefault("HUGGING_FACE_API_KEY", "test-only-token")
import asyncio
import httpx
import pytest
import main
from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def reset(monkeypatch):
    main.request_windows.clear()
    monkeypatch.setattr(main,'API_ACCESS_KEY','access-test-key')
    monkeypatch.setattr(main,'RATE_LIMIT_REQUESTS',2)
    async def fake(*args): return 'ok'
    monkeypatch.setattr(main,'call_llm',fake)

@pytest.mark.parametrize('path', ['/chat','/test-api'])
def test_authentication_blocks_provider(monkeypatch,path):
    async def fail(*args): pytest.fail('unauthorized provider call')
    monkeypatch.setattr(main,'call_llm',fail)
    client=TestClient(main.app)
    for headers in [{},{'Authorization':'Bearer wrong'}]:
        r=client.post(path,json={'message':'hi'},headers=headers) if path=='/chat' else client.get(path,headers=headers)
        assert r.status_code==401

def test_shared_limit_and_expiry(monkeypatch):
    clock=[100.0]
    monkeypatch.setattr(main.time,'monotonic',lambda:clock[0])
    client=TestClient(main.app)
    headers={'Authorization':'Bearer access-test-key'}
    assert client.post('/chat',json={'message':'hi'},headers=headers).status_code==200
    assert client.get('/test-api',headers=headers).status_code==200
    r=client.post('/chat',json={'message':'hi'},headers=headers)
    assert r.status_code==429
    assert int(r.headers['Retry-After'])>0
    clock[0]+=61
    assert client.post('/chat',json={'message':'hi'},headers=headers).status_code==200

def test_static_does_not_need_key_or_consume_limit():
    client=TestClient(main.app)
    for _ in range(4): assert client.get('/hello').status_code==200
    assert main.request_windows=={}

def test_local_mode(monkeypatch):
    monkeypatch.setattr(main,'API_ACCESS_KEY','')
    assert TestClient(main.app).post('/chat',json={'message':'hi'}).status_code==200

def test_forwarded_header_cannot_bypass_limit():
    client=TestClient(main.app)
    for i in range(3):
        r=client.post('/chat',json={'message':'hi'},headers={'Authorization':'Bearer access-test-key','X-Forwarded-For':str(i)})
    assert r.status_code==429

def test_limiter_capacity_is_bounded(monkeypatch):
    monkeypatch.setattr(main, 'MAX_RATE_LIMIT_CLIENTS', 1)
    main.request_windows['another-client'] = main.deque([main.time.monotonic()])
    response = TestClient(main.app).post('/chat', json={'message': 'hi'}, headers={'Authorization': 'Bearer access-test-key'})
    assert response.status_code == 503
    assert len(main.request_windows) == 1
