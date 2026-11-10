from datetime import date
from pathlib import Path
from threading import Event

import pytest

from collector.browser import require_authorization
from collector.data import export_csv
from collector.fixture_worker import collect_fixture


def test_gate(monkeypatch):
    monkeypatch.delenv('ENABLE_PERMITTED_BROWSER', raising=False)
    with pytest.raises(PermissionError):
        require_authorization(True)
    monkeypatch.setenv('ENABLE_PERMITTED_BROWSER', 'true')
    monkeypatch.delenv('BROWSER_AUTHORIZATION_REFERENCE', raising=False)
    with pytest.raises(PermissionError):
        require_authorization(True)
    monkeypatch.setenv('BROWSER_AUTHORIZATION_REFERENCE', 'documented-method-approval')
    with pytest.raises(PermissionError):
        require_authorization(False)


def test_fixture_browser():
    records, issues = collect_fixture(Path('tests/fixtures/channel.html').read_bytes(),
                                     'https://www.tiktok.com/@masterart_th', date(2026, 10, 1), date(2026, 10, 31))
    assert not issues and len(records) == 1
    assert records[0]['source_type'] == 'fixture'
    assert records[0]['caption'] == 'ทดสอบ ศิลปะ 🎨, "สีสวย"'
    assert records[0]['views'] is None
    assert records[0]['views_displayed'] == '104K'
    assert records[0]['likes'] == 0
    assert 'ทดสอบ'.encode() in export_csv(records)


def test_cancel_before_navigation():
    event = Event()
    event.set()
    records, issues = collect_fixture(b'', 'https://www.tiktok.com/@masterart_th', date(2026, 10, 1), date(2026, 10, 31), event)
    assert records == [] and issues[0]['kind'] == 'cancelled'
