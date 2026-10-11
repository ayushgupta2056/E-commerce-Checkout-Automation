from playwright.sync_api import Page, expect


class CartPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def open(self) -> None:
        self.page.goto(f"{self.base_url}/cart", wait_until="domcontentloaded")

    # The cart forms post back to /cart, so the URL does not change. Wait for the
    # reloaded page before returning, otherwise amount() can read the old totals.
    def update_quantity(self, product_id: int, quantity: int) -> None:
        self.page.get_by_test_id(f"cart-quantity-{product_id}").fill(str(quantity))
        with self.page.expect_navigation():
            self.page.get_by_test_id(f"update-item-{product_id}").click(force=True)

    def remove_item(self, product_id: int) -> None:
        with self.page.expect_navigation():
            self.page.get_by_test_id(f"remove-item-{product_id}").click(force=True)

    def apply_discount(self, code: str) -> None:
        self.page.get_by_test_id("discount-code-input").fill(code)
        with self.page.expect_navigation():
            self.page.get_by_test_id("apply-discount-button").click(force=True)

    def checkout(self) -> None:
        self.page.get_by_test_id("checkout-link").click(no_wait_after=True)

    def amount(self, test_id: str) -> float:
        return float(self.page.get_by_test_id(test_id).inner_text().replace("$", ""))

    def expect_item(self, product_id: int) -> None:
        expect(self.page.get_by_test_id(f"cart-row-{product_id}")).to_be_visible()

    def expect_empty(self) -> None:
        expect(self.page.get_by_test_id("empty-cart-message")).to_be_visible()

    def expect_error(self, message: str) -> None:
        expect(self.page.get_by_test_id("error-message")).to_contain_text(message)
