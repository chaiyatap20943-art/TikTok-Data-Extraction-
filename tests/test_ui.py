from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_private_gate(monkeypatch):
    monkeypatch.delenv('PILOT_PASSWORD', raising=False)
    app = AppTest.from_file(str(Path('app.py').resolve())).run()
    assert not app.exception
    assert 'unavailable' in app.error[0].value
    assert not app.text_input


def test_signin_and_default_controls(monkeypatch):
    monkeypatch.setenv('PILOT_PASSWORD', 'synthetic-test-password-only')
    app = AppTest.from_file(str(Path('app.py').resolve())).run()
    app.text_input[0].set_value('wrong')
    app.button[0].click().run()
    assert app.error[0].value == 'Incorrect password.'
    app.session_state['retry_after'] = 0
    app.text_input[0].set_value('synthetic-test-password-only')
    app.button[0].click().run()
    assert not app.exception
    assert app.text_input[0].value.endswith('@masterart_th')
    assert str(app.date_input[0].value) == '2026-10-01'
    app.radio[0].set_value('Authorized browser collection').run()
    assert any('documentary' in error.value for error in app.error)
    assert any(button.disabled for button in app.button if button.label == 'Start browser collection')
