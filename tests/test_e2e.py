"""Actual browser upload/review/download against a running local Streamlit server."""
import csv
import io
import os
import secrets
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright


def test_streamlit_csv_download(tmp_path):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    password = secrets.token_urlsafe(24)
    environment = {**os.environ, 'PILOT_PASSWORD': password}
    process = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', 'app.py', '--server.headless=true',
                                f'--server.port={port}', '--browser.gatherUsageStats=false'],
                               env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f'http://127.0.0.1:{port}'
    try:
        for _ in range(100):
            try:
                with urllib.request.urlopen(base + '/_stcore/health', timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(.1)
        else:
            raise AssertionError('Streamlit failed to start')
        with sync_playwright() as driver:
            browser = driver.chromium.launch(headless=True, executable_path=shutil.which('chromium'))
            try:
                page = browser.new_page()
                page.set_default_timeout(15000)
                page.goto(base)
                page.get_by_label('Pilot password', exact=True).fill(password)
                page.get_by_role('button', name='Sign in', exact=True).click()
                page.get_by_text('I am authorized to process these uploaded sources.', exact=True).click()
                fixture = ('publication_datetime,caption,video_url,views,likes,comments,shares,saves,video_url_quality,caption_quality\n'
                           '2026-10-01T00:00:00+07:00,ศิลปะ 🎨,https://www.tiktok.com/@masterart_th/video/1000000000000000001,104K,0,12,,,verified,full\n')
                page.locator('input[type=file]').set_input_files({'name': 'synthetic.csv', 'mimeType': 'text/csv', 'buffer': fixture.encode('utf-8-sig')})
                page.get_by_role('button', name='Import & process', exact=True).click()
                page.get_by_text('1 source rows processed; 1 included; 0 excluded or invalid.', exact=True).wait_for()
                with page.expect_download() as download:
                    page.get_by_role('button', name='Download CSV', exact=True).click()
                path = tmp_path / 'download.csv'
                download.value.save_as(path)
                payload = path.read_bytes()
                parsed = list(csv.DictReader(io.StringIO(payload.decode('utf-8-sig'))))
                assert parsed[0]['caption'] == 'ศิลปะ 🎨'
                assert parsed[0]['views'] == ''
                assert parsed[0]['views_displayed'] == '104K'
                assert parsed[0]['likes'] == '0'
                assert parsed[0]['shares'] == ''
                assert parsed[0]['posted_at_bangkok'] == '2026-10-01T00:00:00+07:00'
                assert download.value.suggested_filename.startswith('tiktok_masterart_th_2026-10-01_2026-10-31_')
                page.get_by_role('button', name='Download Coverage Report', exact=True).wait_for()
                artifacts = Path('artifacts')
                artifacts.mkdir(exist_ok=True)
                page.screenshot(path=str(artifacts / 'synthetic-review.png'), full_page=True)
                page.get_by_role('button', name='Delete session data and sign out').click()
                page.get_by_label('Pilot password', exact=True).wait_for()
            finally:
                browser.close()
    finally:
        process.terminate()
        process.wait(timeout=10)
