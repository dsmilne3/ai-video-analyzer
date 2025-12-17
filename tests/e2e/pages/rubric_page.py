class RubricPage:
    def __init__(self, page):
        self.page = page

    def navigate_manage(self):
        self.page.get_by_role("link", name="Manage Rubrics").click()
        self.page.wait_for_load_state("networkidle")

    def navigate_create(self):
        self.page.get_by_role("link", name="Create Rubric").click()
        self.page.wait_for_load_state("networkidle")

    def create_simple_rubric(self, name="e2e-rubric"):
        # Fill the basic info and submit; page auto-adds default categories
        self.page.get_by_label("Rubric Name").fill(name)
        self.page.get_by_role("button", name="Create Rubric").click()
        self.page.wait_for_load_state("networkidle")

    def creation_success(self):
        # Success message contains "Rubric 'NAME' created successfully!"
        try:
            # Wait up to 5s for a success alert mentioning creation
            locator = self.page.get_by_role("alert").filter(has_text="created successfully").first
            locator.wait_for(state="visible", timeout=5000)
            return True
        except Exception:
            try:
                self.page.get_by_text("created successfully").first.wait_for(state="visible", timeout=5000)
                return True
            except Exception:
                return False
