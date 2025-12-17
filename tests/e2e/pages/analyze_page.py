import re


class AnalyzePage:
    def __init__(self, page):
        self.page = page

    def navigate(self):
        self.page.get_by_role("link", name="Analyze Video").click()
        self.page.wait_for_load_state("networkidle")

    def upload_video(self, filepath):
        self.page.set_input_files("input[type='file']", filepath)

    def select_rubric(self, name):
        # Disambiguate by ARIA name: 'Evaluation Rubric'
        self.page.get_by_role("combobox", name=re.compile("Evaluation Rubric", re.I)).click()
        # Try selecting by provided name; fallback to first option quickly
        try:
            opt = self.page.get_by_role("option", name=re.compile(re.escape(name), re.I)).first
            opt.click()
        except Exception:
            self.page.get_by_role("option").first.click()

    def select_any_rubric(self):
        # Open rubric combobox and choose the first available option
        self.page.get_by_role("combobox", name=re.compile("Evaluation Rubric", re.I)).click()
        self.page.get_by_role("option").first.click()

    def fill_submitter_info(self, first="Test", last="User", partner="Demo"):
        self.page.get_by_label("First Name").fill(first)
        self.page.get_by_label("Last Name").fill(last)
        self.page.get_by_label("Partner Name").fill(partner)

    def start_analysis(self):
        self.page.get_by_role("button", name="Analyze").click()
        self.page.wait_for_load_state("networkidle")

    def results_visible(self):
        return self.page.locator("text=Results").first.is_visible()

    def error_text(self):
        # Streamlit alerts often render with role="alert"; collect all and join
        try:
            alerts = self.page.get_by_role("alert")
            texts = alerts.all_text_contents()
            if texts:
                return "\n".join(texts)
        except Exception:
            pass
        try:
            return self.page.locator(".stAlert").first.inner_text()
        except Exception:
            return ""
