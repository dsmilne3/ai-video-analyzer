import os
import time
import subprocess
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def streamlit_url():
    """Start the Streamlit app in headless mode on a fixed port and yield its URL."""
    env = os.environ.copy()
    cmd = ["./run.sh", "app", "--server.headless", "true", "--server.port", "8502"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(5)
    yield "http://localhost:8502"
    try:
        proc.terminate()
        proc.wait(timeout=10)
    except Exception:
        proc.kill()

@pytest.fixture(scope="function")
def page(streamlit_url):
    """Provide a Playwright page connected to the running app."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        pg = context.new_page()
        pg.goto(streamlit_url)
        yield pg
        context.close()
        browser.close()
import pytest
import subprocess
import time
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def streamlit_app():
    """Start Streamlit app in background, yield URL, cleanup on exit."""
    process = subprocess.Popen(
        ["./run.sh", "app", "--server.headless", "true", "--server.port", "8502"],
        cwd="/Users/davidmilne/Projects/ai-video-analyzer"
    )
    time.sleep(5)  # Wait for app to start
    yield "http://localhost:8502"
    process.terminate()
    process.wait()

@pytest.fixture(scope="function")
def browser_context(streamlit_app):
    """Create browser context for each test."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(streamlit_app)
        yield page
        context.close()
        browser.close()