import os
os.environ.setdefault("HUGGING_FACE_API_KEY", "test-only-token")
import asyncio
import httpx
import pytest
import main
from fastapi.testclient import TestClient

def test_static_and_health():
    client=TestClient(main.app)
    assert client.get('/').status_code==200
    assert client.get('/static/script.js').status_code==200
    assert client.get('/hello').json()=={"message":"Hello, World!"}

def test_chat_without_network(monkeypatch):
    async def fake(*args): return 'Test answer'
    monkeypatch.setattr(main,'call_llm',fake)
    assert TestClient(main.app).post('/chat',json={"message":"Hi"}).json()['response']=='Test answer'

def test_missing_token_fails_with_clear_message():
    import subprocess,sys,tempfile
    env={**os.environ,'HUGGING_FACE_API_KEY':''}
    env['PYTHONPATH']=os.getcwd()
    with tempfile.TemporaryDirectory() as directory:
        result=subprocess.run([sys.executable,'-c','import main'],env=env,cwd=directory,capture_output=True,text=True)
    assert result.returncode!=0
    assert 'HUGGING_FACE_API_KEY' in result.stderr
