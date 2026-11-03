from pathlib import Path
from playwright.sync_api import expect


def test_access_key_is_sent_in_header_only(page):
    page.set_content(Path('static/index.html').read_text())
    page.add_script_tag(path='static/script.js')
    page.evaluate("""() => {
        window.sent = [];
        window.fetch = async (url, options) => {
            sent.push({url, headers: options.headers, body: JSON.parse(options.body)});
            return {ok: true, json: async () => ({response: 'ok'})};
        };
    }""")
    page.locator('#access-key').fill('private-access-key')
    page.locator('#user-input').fill('hi')
    page.locator('#send-btn').click()
    expect(page.locator('.bot-message').last).to_contain_text('ok')
    sent = page.evaluate('sent[0]')
    assert sent['headers']['Authorization'] == 'Bearer private-access-key'
    assert 'private-access-key' not in sent['url']
    assert 'private-access-key' not in str(sent['body'])
    assert page.locator('#access-key').get_attribute('type') == 'password'
