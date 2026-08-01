from playwright.sync_api import Page, expect


class CheckoutPage:
    def __init__(self, page: Page):
        self.page = page

    def submit(self, full_name: str = "", address: str = "", city: str = "", zip_code: str = "") -> None:
        self.page.get_by_test_id("full-name-input").fill(full_name)
        self.page.get_by_test_id("address-input").fill(address)
        self.page.get_by_test_id("city-input").fill(city)
        self.page.get_by_test_id("zip-input").fill(zip_code)
        self.page.get_by_test_id("continue-payment-button").click(force=True, no_wait_after=True)

    def expect_error(self, message: str) -> None:
        expect(self.page.get_by_test_id("error-message")).to_contain_text(message)
