"""Bounded browser evidence capture; never promises complete TikTok extraction."""
import os
import shutil
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

from collector.data import channel_handle

ALLOWED_HOSTS = {'www.tiktok.com', 'tiktok.com'}


def require_authorization(authorized):
    if os.environ.get('ENABLE_PERMITTED_BROWSER') != 'true':
        raise PermissionError('Browser access is disabled by the operator.')
    if not os.environ.get('BROWSER_AUTHORIZATION_REFERENCE'):
        raise PermissionError('Operator documentary authorization reference is required.')
    if not authorized:
        raise PermissionError('Explicit source authorization is required.')


def capture_channel(url, authorized=False):
    require_authorization(authorized)
    handle = channel_handle(url)
    with sync_playwright() as driver:
        browser = driver.chromium.launch(headless=True, executable_path=shutil.which('chromium'))
        try:
            context = browser.new_context(service_workers='block', accept_downloads=False)

            def route_request(route):
                target = urlsplit(route.request.url)
                if target.scheme == 'https' and target.hostname in ALLOWED_HOSTS and target.port in (None, 443):
                    route.continue_()
                else:
                    route.abort()

            context.route('**/*', route_request)
            page = context.new_page()
            response = page.goto(f'https://www.tiktok.com/@{handle}', wait_until='domcontentloaded', timeout=30000)
            if response is None or response.status >= 400:
                raise RuntimeError('Source refused access. Stop and use an authorized import.')
            text = page.locator('body').inner_text(timeout=10000)
            if any(word in text.lower() for word in ('captcha', 'verify to continue', 'log in', 'access denied')):
                raise RuntimeError('Authentication or an access challenge was detected. Collection stopped.')
            return {'text': text[:100000], 'screenshot': page.screenshot(full_page=False)}
        finally:
            browser.close()
