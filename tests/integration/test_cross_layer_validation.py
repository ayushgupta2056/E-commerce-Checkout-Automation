import pytest

from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from pages.order_confirmation_page import OrderConfirmationPage
from pages.payment_page import PaymentPage
from pages.product_details_page import ProductDetailsPage
from pages.products_page import ProductsPage
from tests.test_data.test_data import PRODUCTS, VALID_PAYMENT


@pytest.mark.integration
def test_cart_totals_match_ui_api_and_database(authenticated_page, base_url, api_client, db_client):
    products = ProductsPage(authenticated_page, base_url)
    products.open()
    products.open_product(PRODUCTS["mouse"])
    ProductDetailsPage(authenticated_page).add_to_cart(2)

    products.open()
    products.open_product(PRODUCTS["hub"])
    ProductDetailsPage(authenticated_page).add_to_cart(1)

    cart_page = CartPage(authenticated_page, base_url)
    cart_page.apply_discount("SAVE10")
    ui_totals = {
        "subtotal": cart_page.amount("subtotal"),
        "tax": cart_page.amount("tax"),
        "discount": cart_page.amount("discount"),
        "final_total": cart_page.amount("final-total"),
    }

    api_cart = api_client.view_cart().json()
    db_cart = db_client.execute_select_one("SELECT * FROM carts WHERE user_id = ?", (api_client.user_id,))
    db_items = db_client.execute_select_many(
        """
        SELECT ci.product_id, ci.quantity, p.price
        FROM cart_items ci
        JOIN products p ON p.product_id = ci.product_id
        WHERE ci.cart_id = ?
        ORDER BY ci.product_id
        """,
        (db_cart["cart_id"],),
    )

    assert ui_totals["subtotal"] == api_cart["subtotal"]
    assert ui_totals["tax"] == api_cart["tax"]
    assert ui_totals["discount"] == api_cart["discount"]
    assert ui_totals["final_total"] == api_cart["final_total"]
    assert [(item["product_id"], item["quantity"]) for item in api_cart["items"]] == [
        (item["product_id"], item["quantity"]) for item in db_items
    ]


@pytest.mark.integration
def test_order_and_payment_match_ui_api_and_database(authenticated_page, base_url, api_client, db_client):
    products = ProductsPage(authenticated_page, base_url)
    products.open()
    products.open_product(PRODUCTS["keyboard"])
    ProductDetailsPage(authenticated_page).add_to_cart(1)

    CartPage(authenticated_page, base_url).checkout()
    CheckoutPage(authenticated_page).submit("Test User", "100 Main Street", "Austin", "73301")
    PaymentPage(authenticated_page).pay(**VALID_PAYMENT)

    confirmation = OrderConfirmationPage(authenticated_page)
    confirmation.expect_confirmed()
    order_id = confirmation.order_id()

    api_order = api_client.request("GET", f"/api/orders/{order_id}").json()
    db_order = db_client.execute_select_one("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    db_items = db_client.execute_select_many("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
    db_payment = db_client.execute_select_one("SELECT * FROM payments WHERE order_id = ?", (order_id,))

    assert api_order["order_id"] == db_order["order_id"] == order_id
    assert api_order["user_id"] == db_order["user_id"] == api_client.user_id
    assert api_order["subtotal"] == db_order["subtotal"]
    assert api_order["tax"] == db_order["tax"]
    assert api_order["discount"] == db_order["discount"]
    assert api_order["final_total"] == db_order["final_total"] == db_payment["amount"]
    assert api_order["items"][0]["product_id"] == db_items[0]["product_id"] == PRODUCTS["keyboard"]
    assert db_payment["payment_status"] == "SUCCESS"
    assert db_payment["last_four_card_digits"] == "1111"
