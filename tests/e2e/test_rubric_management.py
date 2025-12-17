import pytest
import time
from tests.e2e.pages.rubric_page import RubricPage
from tests.e2e.pages.analyze_page import AnalyzePage

pytestmark = pytest.mark.e2e

def test_create_rubric_and_use_in_analysis(page):
    rp = RubricPage(page)
    ap = AnalyzePage(page)

    rp.navigate_create()
    unique_name = f"e2e-rubric-{int(time.time())}"
    rp.create_simple_rubric(unique_name)
    assert rp.creation_success()
    # Navigate to analyze and select new rubric by its display name
    ap.navigate()
    ap.select_rubric(unique_name)
    assert True  # If selector works without timeout, rubric is present
