from playwright.sync_api import Page, expect


class ProductsPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def open(self) -> None:
        self.page.goto(f"{self.base_url}/products", wait_until="domcontentloaded")

    def search(self, text: str) -> None:
        self.page.get_by_test_id("search-input").fill(text)
        self.page.get_by_test_id("search-button").click()

    def open_product(self, product_id: int) -> None:
        self.page.get_by_test_id(f"details-link-{product_id}").click()

    def expect_product_visible(self, product_id: int) -> None:
        expect(self.page.get_by_test_id(f"product-card-{product_id}")).to_be_visible()

    def expect_no_products(self) -> None:
        expect(self.page.get_by_test_id("no-products-message")).to_be_visible()
