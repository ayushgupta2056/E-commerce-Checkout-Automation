from playwright.sync_api import Page, expect


class CartPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def open(self) -> None:
        self.page.goto(f"{self.base_url}/cart", wait_until="domcontentloaded")

    def update_quantity(self, product_id: int, quantity: int) -> None:
        self.page.get_by_test_id(f"cart-quantity-{product_id}").fill(str(quantity))
        self.page.get_by_test_id(f"update-item-{product_id}").click(force=True, no_wait_after=True)

    def remove_item(self, product_id: int) -> None:
        self.page.get_by_test_id(f"remove-item-{product_id}").click(force=True, no_wait_after=True)

    def apply_discount(self, code: str) -> None:
        self.page.get_by_test_id("discount-code-input").fill(code)
        self.page.get_by_test_id("apply-discount-button").click(force=True, no_wait_after=True)

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
