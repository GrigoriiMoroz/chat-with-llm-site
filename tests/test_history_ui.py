from pathlib import Path
from playwright.sync_api import expect

def test_history_and_reset(page):
    page.set_content(Path('static/index.html').read_text())
    page.add_script_tag(path='static/script.js')
    page.evaluate("() => { window.requests=[];window.fetch=async(u,o)=>{requests.push(JSON.parse(o.body));return {ok:true,json:async()=>({response:'answer'})}}; }")
    page.locator('#user-input').fill('My name is Greg')
    page.locator('#send-btn').click()
    expect(page.locator('.bot-message').last).to_contain_text('answer')
    page.locator('#user-input').fill('What is my name?')
    page.locator('#send-btn').click()
    expect(page.locator('.user-message')).to_have_count(2)
    assert page.evaluate('requests[1].history')==[{'role':'user','content':'My name is Greg'},{'role':'assistant','content':'answer'}]
    page.get_by_role('button',name='Новый чат').click()
    expect(page.locator('#messages')).to_be_empty()
    page.locator('#user-input').fill('New topic')
    page.locator('#send-btn').click()
    assert page.evaluate('requests[2].history')==[]

def test_context_is_bounded_and_isolated(page, context):
    page.set_content(Path('static/index.html').read_text())
    page.add_script_tag(path='static/script.js')
    page.evaluate("() => { window.fetch=async()=>({ok:true,json:async()=>({response:'answer'})}); }")
    page.evaluate("async()=>{for(let i=0;i<15;i++){userInput.value='message '+i;await sendMessage();}}")
    assert page.evaluate('conversationHistory.length')==20
    other=context.new_page()
    other.set_content(Path('static/index.html').read_text())
    other.add_script_tag(path='static/script.js')
    assert other.evaluate('conversationHistory.length')==0


def test_failed_turn_is_not_saved(page):
    page.set_content(Path('static/index.html').read_text())
    page.add_script_tag(path='static/script.js')
    page.evaluate("() => { window.fetch=async()=>({ok:false,json:async()=>({detail:{message:'upstream unavailable'}})}); }")
    page.locator('#user-input').fill('hi')
    page.locator('#send-btn').click()
    expect(page.locator('.bot-message').last).to_contain_text('upstream unavailable')
    assert page.evaluate('conversationHistory.length') == 0
