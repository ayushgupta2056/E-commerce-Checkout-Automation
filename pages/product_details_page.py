from playwright.sync_api import Page, TimeoutError, expect


class ProductDetailsPage:
    def __init__(self, page: Page):
        self.page = page

    def add_to_cart(self, quantity: int = 1) -> None:
        self.page.get_by_test_id("quantity-input").fill(str(quantity))
        self.page.get_by_test_id("add-to-cart-button").click(force=True, no_wait_after=True)
        try:
            self.page.wait_for_url("**/cart", timeout=5000)
        except TimeoutError:
            pass

    def expect_loaded(self, product_name: str) -> None:
        expect(self.page.get_by_test_id("product-name")).to_contain_text(product_name)

    def expect_error(self, message: str) -> None:
        expect(self.page.get_by_test_id("error-message")).to_contain_text(message)
