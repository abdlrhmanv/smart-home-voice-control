"""Optional Playwright UI flows (home → password → voice locked gate).

  pip install -r requirements-dev.txt
  playwright install chromium
  RUN_UI_E2E=1 pytest tests/test_ui_smoke.py -q
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture(scope="module")
def streamlit_server():
    if os.environ.get("RUN_UI_E2E") != "1":
        pytest.skip("Set RUN_UI_E2E=1 to run Streamlit UI e2e")
    pytest.importorskip("playwright")

    port = _free_port()
    env = os.environ.copy()
    env["ARDUINO_PORT"] = ""
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(ROOT / "app.py"),
            "--server.headless",
            "true",
            "--server.port",
            str(port),
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.time() + 90
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                break
        except OSError:
            if proc.poll() is not None:
                pytest.fail("Streamlit exited early")
            time.sleep(0.5)
    else:
        proc.kill()
        pytest.fail("Streamlit did not start")

    yield f"http://127.0.0.1:{port}"
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.mark.ui
def test_home_loads(streamlit_server):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(streamlit_server, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(2500)
        assert "smart home" in page.content().lower()
        browser.close()


@pytest.mark.ui
def test_password_page_loads(streamlit_server):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(
            f"{streamlit_server}/Password",
            wait_until="domcontentloaded",
            timeout=60_000,
        )
        page.wait_for_timeout(2500)
        body = page.content().lower()
        assert "password" in body or "authentication" in body or "open sesame" in body
        browser.close()


@pytest.mark.ui
def test_voice_page_shows_lock_gate(streamlit_server):
    """Unauthenticated session should see the lock warning (no mic needed)."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(
            f"{streamlit_server}/Voice_Control",
            wait_until="domcontentloaded",
            timeout=60_000,
        )
        page.wait_for_timeout(3000)
        body = page.content().lower()
        assert "locked" in body or "authenticate" in body or "password" in body
        browser.close()


@pytest.mark.ui
def test_password_page_accepts_wav_upload_widget(streamlit_server):
    """Uploader is present so Playwright can inject fixtures without a mic."""
    from playwright.sync_api import sync_playwright

    fixture = ROOT / "tests" / "fixtures" / "audio" / "noise.wav"
    if not fixture.exists():
        sys.path.insert(0, str(ROOT / "ml"))
        from make_fixtures import write_fixtures

        write_fixtures(fixture.parent)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(
            f"{streamlit_server}/Password",
            wait_until="domcontentloaded",
            timeout=60_000,
        )
        page.wait_for_timeout(2500)
        # Streamlit file_uploader renders an <input type="file">
        file_input = page.locator('input[type="file"]')
        assert file_input.count() >= 1
        file_input.first.set_input_files(str(fixture))
        page.wait_for_timeout(1500)
        body = page.content().lower()
        assert "verify uploaded password" in body or "upload" in body
        browser.close()
