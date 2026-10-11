"""Open defects found on 2026-10-11 while preparing the interview demo.

Each test asserts the expected behaviour and is marked xfail(strict=True):
it is reported as XFAIL while the defect exists, and turns into a failure
(XPASS strict) once the defect is fixed, so the marker gets removed.
See docs/jira/DEFECT-004 to DEFECT-006.
"""
import pytest

from tests.test_data.test_data import PRODUCTS, VALID_PAYMENT


@pytest.mark.api
@pytest.mark.xfail(strict=True, reason="DEFECT-004: an already paid order can be paid again")
def test_paid_order_cannot_be_paid_twice(api_client):
    api_client.add_to_cart(PRODUCTS["headphones"], 2)
    order_id = api_client.create_order().json()["order_id"]
    first = api_client.pay(order_id, VALID_PAYMENT)
    assert first.json()["payment_status"] == "SUCCESS"

    second = api_client.pay(order_id, VALID_PAYMENT)

    stock = api_client.request("GET", f"/api/products/{PRODUCTS['headphones']}").json()["stock_quantity"]
    assert second.status_code in (400, 409)
    assert stock == 3


@pytest.mark.api
@pytest.mark.xfail(strict=True, reason="DEFECT-005: expiration date month and expiry are not validated")
@pytest.mark.parametrize("expiration_date", ["13/30", "ab/cd", "01/20"])
def test_invalid_or_expired_card_is_rejected(api_client, expiration_date):
    api_client.add_to_cart(PRODUCTS["mouse"], 1)
    order_id = api_client.create_order().json()["order_id"]

    response = api_client.pay(order_id, {**VALID_PAYMENT, "expiration_date": expiration_date})

    assert response.status_code == 400


@pytest.mark.api
@pytest.mark.xfail(strict=True, reason="DEFECT-006: non-numeric product_id returns HTTP 500")
def test_non_numeric_product_id_returns_client_error(api_client):
    response = api_client.request(
        "POST",
        "/api/cart/items",
        json={"user_id": api_client.user_id, "product_id": "abc", "quantity": 1},
    )

    assert response.status_code == 400
