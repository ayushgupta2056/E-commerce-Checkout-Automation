import pytest

from tests.test_data.test_data import DECLINED_PAYMENT, INVALID_USER, PRODUCTS, VALID_PAYMENT, VALID_USER
from utilities.price_calculator import calculate_totals


@pytest.mark.api
def test_login_products_and_product_errors(api_client):
    login = api_client.login(VALID_USER["email"], VALID_USER["password"])
    assert login.status_code == 200
    assert login.json()["email"] == VALID_USER["email"]

    invalid = api_client.login(INVALID_USER["email"], INVALID_USER["password"])
    assert invalid.status_code == 401
    assert invalid.json()["error"] == "Invalid email or password."

    products = api_client.request("GET", "/api/products")
    assert products.status_code == 200
    assert len(products.json()["products"]) >= 5

    search = api_client.request("GET", "/api/products", params={"search": "Mouse"})
    assert search.status_code == 200
    assert search.json()["products"][0]["product_id"] == PRODUCTS["mouse"]

    product = api_client.request("GET", f"/api/products/{PRODUCTS['keyboard']}")
    assert product.status_code == 200
    assert product.json()["name"] == "Mechanical Keyboard"

    missing = api_client.request("GET", "/api/products/99999")
    assert missing.status_code == 404


@pytest.mark.api
def test_cart_discount_order_and_successful_payment(api_client):
    add = api_client.add_to_cart(PRODUCTS["mouse"], 2)
    assert add.status_code == 200

    update = api_client.update_cart_item(PRODUCTS["mouse"], 3)
    assert update.status_code == 200
    assert update.json()["items"][0]["quantity"] == 3

    discount = api_client.apply_discount("SAVE10")
    assert discount.status_code == 200
    expected = calculate_totals(24.99 * 3, "SAVE10")
    assert discount.json()["subtotal"] == expected["subtotal"]
    assert discount.json()["tax"] == expected["tax"]
    assert discount.json()["discount"] == expected["discount"]
    assert discount.json()["final_total"] == expected["final_total"]

    order = api_client.create_order()
    assert order.status_code == 201
    order_id = order.json()["order_id"]

    payment = api_client.pay(order_id, VALID_PAYMENT)
    assert payment.status_code == 200
    assert payment.json()["payment_status"] == "SUCCESS"
    assert payment.json()["last_four_card_digits"] == "1111"

    fetched = api_client.request("GET", f"/api/orders/{order_id}")
    assert fetched.status_code == 200
    assert fetched.json()["order_status"] == "PAID"


@pytest.mark.api
def test_cart_negative_paths_declined_payment_and_failed_response(api_client):
    out_of_stock = api_client.add_to_cart(PRODUCTS["out_of_stock"], 1)
    assert out_of_stock.status_code == 409

    api_client.add_to_cart(PRODUCTS["headphones"], 1)
    over_stock = api_client.update_cart_item(PRODUCTS["headphones"], 99)
    assert over_stock.status_code == 409

    invalid_discount = api_client.apply_discount("BADCODE")
    assert invalid_discount.status_code == 400

    remove = api_client.remove_cart_item(PRODUCTS["headphones"])
    assert remove.status_code == 200
    empty_order = api_client.create_order()
    assert empty_order.status_code == 400

    api_client.add_to_cart(PRODUCTS["mouse"], 1)
    order = api_client.create_order()
    declined = api_client.pay(order.json()["order_id"], DECLINED_PAYMENT)
    assert declined.status_code == 200
    assert declined.json()["payment_status"] == "DECLINED"

    missing_order = api_client.request("GET", "/api/orders/99999")
    assert missing_order.status_code == 404

    failed = api_client.request("GET", "/api/simulate-error")
    assert failed.status_code == 500
