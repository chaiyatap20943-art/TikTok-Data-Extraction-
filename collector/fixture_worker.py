"""Local test adapter. This is explicitly synthetic and cannot target TikTok."""
import threading
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import sync_playwright

from collector.data import INPUT_FIELDS, normalize_rows


def collect_fixture(html, channel, start, end, cancel=None):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        if cancel and cancel.is_set():
            return [], [{'kind': 'cancelled', 'reason': 'Cancelled before navigation'}]
        with sync_playwright() as driver:
            browser = driver.chromium.launch(headless=True, executable_path=shutil.which('chromium'))
            try:
                page = browser.new_page()
                page.set_default_timeout(5000)
                page.goto(f'http://127.0.0.1:{server.server_port}', timeout=10000)
                page.get_by_role('textbox').fill('synthetic')
                page.get_by_role('button', name='Load videos').scroll_into_view_if_needed()
                page.get_by_role('button', name='Load videos').click()
                page.get_by_role('button', name='Open video').click()
                if cancel and cancel.is_set():
                    return [], [{'kind': 'cancelled', 'reason': 'Cancelled after navigation'}]
                detail = page.locator('#detail')
                row = {'publication_datetime': detail.get_attribute('data-posted'),
                       'video_url': channel.rstrip('/') + '/video/' + detail.get_attribute('data-video-id'),
                       'video_url_quality': 'verified', 'caption_quality': 'full',
                       'caption': detail.locator('.caption').inner_text(),
                       **{key: detail.locator(f'[data-metric="{key}"]').inner_text()
                          for key in ('views', 'likes', 'comments', 'shares', 'saves')}}
                return normalize_rows([row], dict(zip(INPUT_FIELDS, INPUT_FIELDS)), channel, start, end, 'fixture', 'local synthetic HTML')
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
