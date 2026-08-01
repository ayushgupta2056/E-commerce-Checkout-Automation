import pytest
from playwright.sync_api import expect

from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from pages.login_page import LoginPage
from pages.order_confirmation_page import OrderConfirmationPage
from pages.payment_page import PaymentPage
from pages.product_details_page import ProductDetailsPage
from pages.products_page import ProductsPage
from tests.test_data.test_data import DECLINED_PAYMENT, INVALID_USER, PRODUCTS, VALID_PAYMENT, VALID_USER
from utilities.price_calculator import calculate_totals


@pytest.mark.ui
def test_complete_checkout_with_discount_and_order_history(page, base_url):
    login = LoginPage(page, base_url)
    login.open()
    login.login(VALID_USER["email"], VALID_USER["password"])

    products = ProductsPage(page, base_url)
    products.search("Keyboard")
    products.expect_product_visible(PRODUCTS["keyboard"])
    products.open_product(PRODUCTS["keyboard"])

    details = ProductDetailsPage(page)
    details.expect_loaded("Mechanical Keyboard")
    details.add_to_cart(1)

    products.open()
    products.open_product(PRODUCTS["mouse"])
    details.add_to_cart(2)

    cart = CartPage(page, base_url)
    cart.expect_item(PRODUCTS["keyboard"])
    cart.expect_item(PRODUCTS["mouse"])
    cart.update_quantity(PRODUCTS["mouse"], 3)
    cart.apply_discount("SAVE10")

    expected = calculate_totals(79.99 + (24.99 * 3), "SAVE10")
    assert cart.amount("subtotal") == expected["subtotal"]
    assert cart.amount("tax") == expected["tax"]
    assert cart.amount("discount") == expected["discount"]
    assert cart.amount("final-total") == expected["final_total"]

    cart.checkout()
    checkout = CheckoutPage(page)
    checkout.submit("Test User", "100 Main Street", "Austin", "73301")

    payment = PaymentPage(page)
    payment.pay(**VALID_PAYMENT)

    confirmation = OrderConfirmationPage(page)
    confirmation.expect_confirmed()
    order_id = confirmation.order_id()
    assert order_id > 0

    confirmation.open_history()
    expect(page.get_by_test_id(f"history-order-{order_id}")).to_be_visible()


@pytest.mark.ui
def test_cart_update_and_remove_item(authenticated_page, base_url):
    products = ProductsPage(authenticated_page, base_url)
    products.open()
    products.open_product(PRODUCTS["hub"])
    ProductDetailsPage(authenticated_page).add_to_cart(1)

    cart = CartPage(authenticated_page, base_url)
    cart.update_quantity(PRODUCTS["hub"], 2)
    expect(authenticated_page.get_by_test_id(f"line-total-{PRODUCTS['hub']}")).to_have_text("$99.00")
    assert cart.amount(f"line-total-{PRODUCTS['hub']}") == 99.00
    cart.remove_item(PRODUCTS["hub"])
    cart.expect_empty()


@pytest.mark.ui
def test_invalid_login_and_empty_login_show_errors(page, base_url):
    login = LoginPage(page, base_url)
    login.open()
    login.login(INVALID_USER["email"], INVALID_USER["password"])
    login.expect_error("Invalid email or password.")

    login.login("", "")
    login.expect_error("Email and password are required.")


@pytest.mark.ui
def test_product_search_no_results(authenticated_page, base_url):
    products = ProductsPage(authenticated_page, base_url)
    products.open()
    products.search("does-not-exist")
    products.expect_no_products()


@pytest.mark.ui
def test_out_of_stock_and_over_stock_are_blocked(authenticated_page, base_url):
    products = ProductsPage(authenticated_page, base_url)
    products.open()
    products.open_product(PRODUCTS["out_of_stock"])
    details = ProductDetailsPage(authenticated_page)
    details.add_to_cart(1)
    details.expect_error("Product is out of stock.")

    products.open()
    products.open_product(PRODUCTS["headphones"])
    details.add_to_cart(6)
    details.expect_error("Requested quantity exceeds available stock.")


@pytest.mark.ui
def test_empty_cart_checkout_invalid_discount_checkout_and_payment_errors(authenticated_page, base_url):
    cart = CartPage(authenticated_page, base_url)
    cart.open()
    cart.checkout()
    cart.expect_error("Checkout is not allowed when the cart is empty.")

    products = ProductsPage(authenticated_page, base_url)
    products.open()
    products.open_product(PRODUCTS["mouse"])
    ProductDetailsPage(authenticated_page).add_to_cart(1)
    cart.apply_discount("BADCODE")
    cart.expect_error("Invalid discount code.")

    cart.checkout()
    checkout = CheckoutPage(authenticated_page)
    checkout.submit()
    checkout.expect_error("All checkout fields are required.")
    checkout.submit("Test User", "100 Main Street", "Austin", "73301")

    payment = PaymentPage(authenticated_page)
    payment.pay("", "", "", "")
    payment.expect_error("All payment fields are required.")
    payment.pay("Test User", "123", "12/30", "12")
    payment.expect_error("Card number must be 16 digits.")
    payment.pay(**DECLINED_PAYMENT)
    payment.expect_error("Payment was declined.")
