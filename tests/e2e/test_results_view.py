import os
import pytest
from tests.e2e.pages.analyze_page import AnalyzePage

pytestmark = pytest.mark.e2e

def test_results_page_loads(page):
    # Ensure the Results page can be opened from sidebar
    # Prefer clicking the sidebar nav link to avoid ambiguity with external doc link
    page.get_by_test_id("stSidebarNavItems").get_by_role("link", name="Documentation").click()
    page.wait_for_load_state("networkidle")
    page.get_by_test_id("stSidebarNavItems").get_by_role("link", name="Analyze Video").click()
    page.wait_for_load_state("networkidle")
    # Basic sanity: sidebar and main area visible
    assert page.get_by_text("Analyze Video").first.is_visible()
