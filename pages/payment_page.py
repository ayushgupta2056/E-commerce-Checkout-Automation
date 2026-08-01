from playwright.sync_api import Page, expect


class PaymentPage:
    def __init__(self, page: Page):
        self.page = page

    def pay(self, cardholder_name: str, card_number: str, expiration_date: str, cvv: str) -> None:
        self.page.get_by_test_id("cardholder-input").fill(cardholder_name)
        self.page.get_by_test_id("card-number-input").fill(card_number)
        self.page.get_by_test_id("expiration-input").fill(expiration_date)
        self.page.get_by_test_id("cvv-input").fill(cvv)
        self.page.get_by_test_id("pay-button").click(force=True, no_wait_after=True)

    def expect_error(self, message: str) -> None:
        expect(self.page.get_by_test_id("error-message")).to_contain_text(message)
