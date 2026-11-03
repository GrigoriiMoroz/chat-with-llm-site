from pathlib import Path
import pytest
from playwright.sync_api import expect

@pytest.mark.parametrize('text',['Обычный ответ','<img src=x onerror="window.xss=1">','<script>window.xss=1</script>','<b>bold</b> & text'])
def test_assistant_content_is_plain_text(page,text):
    page.set_content(Path('static/index.html').read_text())
    page.add_script_tag(path='static/script.js')
    page.evaluate('(text)=>addMessage(text,false)',text)
    message=page.locator('.bot-message').last
    expect(message).to_have_text('Assistant: '+text)
    expect(message.locator('strong')).to_have_text('Assistant:')
    expect(message.locator('img,script,b')).to_have_count(0)
    assert page.evaluate('window.xss') is None
