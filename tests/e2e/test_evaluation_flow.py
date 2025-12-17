import os
import pytest
from tests.e2e.pages.analyze_page import AnalyzePage

pytestmark = pytest.mark.e2e

def test_navigate_and_elements(page):
    ap = AnalyzePage(page)
    ap.navigate()
    # Confirm navigation by URL to avoid brittle text checks
    page.wait_for_load_state("networkidle")
    assert "Analyze_Video" in page.url

def test_upload_and_missing_api_key_error(page):
    ap = AnalyzePage(page)
    ap.navigate()
    ap.fill_submitter_info()
    # Create a tiny temporary file with .mp4 extension for upload
    tmp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "tmp_sample.mp4"))
    with open(tmp_path, "wb") as f:
        f.write(b"\x00\x00\x00\x20ftypisom")
    ap.upload_video(tmp_path)
    ap.select_any_rubric()
    ap.start_analysis()
    # Expect an API key error in alert
    text = ap.error_text()
    assert "API key" in text or "OPENAI" in text or "ANTHROPIC" in text
import pytest

@pytest.mark.e2e
def test_navigate_to_analyze_page(page):
    """Verify user can navigate to Analyze Video page."""
    ap = AnalyzePage(page)
    ap.navigate()
    page.wait_for_load_state("networkidle")
    assert "Analyze_Video" in page.url

@pytest.mark.e2e
def test_upload_video_without_api_key(page):
    """Verify error message when API key missing."""
    ap = AnalyzePage(page)
    ap.navigate()
    ap.fill_submitter_info()
    
    # Upload tiny temp file
    tmp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "tmp_sample.mp4"))
    with open(tmp_path, "wb") as f:
        f.write(b"\x00\x00\x00\x20ftypisom")
    page.set_input_files("input[type='file']", tmp_path)
    
    # Select any rubric via page object (scoped combobox)
    ap.select_any_rubric()
    
    # Click analyze without API key
    page.get_by_role("button", name="Analyze").click()
    
    # Expect some alert about keys/providers
    page.wait_for_load_state("networkidle")
    assert page.get_by_role("alert").first.is_visible()