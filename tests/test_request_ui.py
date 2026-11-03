from pathlib import Path
from playwright.sync_api import expect

def load(page):
    page.set_content(Path("static/index.html").read_text())
    page.add_script_tag(path="static/script.js")

def test_pending_blocks_duplicate_requests(page):
    load(page)
    page.evaluate("() => { ""window.calls=0; window.fetch=()=>{ calls++; return new Promise(resolve=>window.finish=()=>resolve({ok:true,json:async()=>({response:'done'})})); };""; }")
    page.locator('#user-input').fill('hello')
    page.locator('#send-btn').click()
    expect(page.locator('#send-btn')).to_be_disabled()
    expect(page.get_by_role('status')).to_have_text('Ассистент отвечает…')
    page.evaluate("sendMessage()")
    assert page.evaluate('calls') == 1
    page.evaluate('finish()')
    expect(page.locator('#send-btn')).to_be_enabled()
    expect(page.get_by_role('status')).to_have_count(0)
    expect(page.locator('.bot-message').last).to_contain_text('done')


def test_timeout_releases_controls(page):
    load(page)
    page.clock.install()
    page.evaluate("""() => { window.fetch=(url, options)=>new Promise((resolve,reject)=>{
        options.signal.addEventListener('abort',()=>reject(new Error('timeout')));
    }); }""")
    page.locator('#user-input').fill('slow request')
    page.locator('#send-btn').click()
    page.clock.fast_forward(65001)
    expect(page.locator('#send-btn')).to_be_enabled()
    expect(page.locator('#user-input')).to_have_value('slow request')

def test_failure_restores_message_and_retry_works(page):
    load(page)
    page.evaluate("() => { window.fetch=async()=>{ throw new Error('offline'); }; }")
    page.locator('#user-input').fill('keep me')
    page.locator('#send-btn').click()
    expect(page.locator('#user-input')).to_have_value('keep me')
    expect(page.locator('#send-btn')).to_be_enabled()
    page.evaluate("() => { window.fetch=async()=>({ok:true,json:async()=>({response:'retried'})}); }")
    page.get_by_role('button',name='Повторить',exact=True).click()
    expect(page.locator('.bot-message').last).to_contain_text('retried')
    expect(page.get_by_role('status')).to_have_count(0)
