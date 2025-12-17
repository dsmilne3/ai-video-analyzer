"""UI Smoke Test: start Streamlit app headless and verify it serves.
Single-user, sequential; no browser automation.
"""
import os
import time
import socket
import urllib.request
import pytest
import shutil
import subprocess
from pathlib import Path

pytestmark = [pytest.mark.integration, pytest.mark.ui_smoke]

APP_PORT = 8501
APP_URL = f"http://localhost:{APP_PORT}"
ROOT_DIR = Path(__file__).parent.parent.parent
RUN_SH = str(ROOT_DIR / 'run.sh')


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        try:
            s.connect(('127.0.0.1', port))
            return True
        except Exception:
            return False


def test_streamlit_app_smoke():
    # Skip if streamlit is not installed
    if shutil.which('streamlit') is None:
        pytest.skip("streamlit not installed; skipping UI smoke test")

    # Start app headless via run.sh
    env = os.environ.copy()
    cmd = [RUN_SH, 'app', '--server.headless', 'true', '--server.port', str(APP_PORT)]
    proc = subprocess.Popen(cmd, cwd=str(ROOT_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    try:
        # Wait for port to open
        deadline = time.time() + 45
        while time.time() < deadline and not _port_open(APP_PORT):
            time.sleep(0.5)
        if not _port_open(APP_PORT):
            stdout, stderr = proc.communicate(timeout=3)
            pytest.fail(f"Streamlit app did not start. stdout={stdout}\nstderr={stderr}")

        # Fetch root page
        with urllib.request.urlopen(APP_URL, timeout=5) as resp:
            body = resp.read().decode('utf-8', errors='ignore')
        assert 'streamlit' in body.lower() or 'body' in body.lower()
    finally:
        # Terminate app
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
