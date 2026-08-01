from playwright.sync_api import Page, expect


class LoginPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def open(self) -> None:
        self.page.goto(f"{self.base_url}/login", wait_until="domcontentloaded")

    def login(self, email: str, password: str) -> None:
        self.page.get_by_test_id("email-input").fill(email)
        self.page.get_by_test_id("password-input").fill(password)
        self.page.get_by_test_id("login-button").click(force=True, no_wait_after=True)

    def expect_error(self, message: str) -> None:
        expect(self.page.get_by_test_id("error-message")).to_contain_text(message)
