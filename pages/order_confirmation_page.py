from playwright.sync_api import Page, expect


class OrderConfirmationPage:
    def __init__(self, page: Page):
        self.page = page

    def order_id(self) -> int:
        return int(self.page.get_by_test_id("order-id").inner_text())

    def expect_confirmed(self) -> None:
        expect(self.page.get_by_test_id("order-confirmation")).to_be_visible()
        expect(self.page.get_by_test_id("order-status")).to_have_text("PAID")

    def open_history(self) -> None:
        self.page.get_by_test_id("order-history-link").click(no_wait_after=True)
