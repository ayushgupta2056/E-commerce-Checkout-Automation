from __future__ import annotations

import requests

from utilities.config_reader import BASE_URL, VALID_USER
from utilities.logger import get_logger


logger = get_logger(__name__)


class ApiClient:
    """Thin requests wrapper with safe logging for API tests."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.user_id: int | None = None

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        logger.info("%s %s", method.upper(), path)
        response = requests.request(method, url, timeout=10, **kwargs)
        logger.info("Response status: %s", response.status_code)
        return response

    def login(self, email: str = VALID_USER["email"], password: str = VALID_USER["password"]) -> requests.Response:
        response = self.request("POST", "/api/login", json={"email": email, "password": password})
        if response.status_code == 200:
            self.user_id = response.json()["user_id"]
        return response

    def add_to_cart(self, product_id: int, quantity: int = 1) -> requests.Response:
        return self.request(
            "POST",
            "/api/cart/items",
            json={"user_id": self.user_id, "product_id": product_id, "quantity": quantity},
        )

    def update_cart_item(self, product_id: int, quantity: int) -> requests.Response:
        return self.request("PUT", f"/api/cart/items/{product_id}", json={"user_id": self.user_id, "quantity": quantity})

    def remove_cart_item(self, product_id: int) -> requests.Response:
        return self.request("DELETE", f"/api/cart/items/{product_id}", params={"user_id": self.user_id})

    def view_cart(self) -> requests.Response:
        return self.request("GET", "/api/cart", params={"user_id": self.user_id})

    def apply_discount(self, discount_code: str) -> requests.Response:
        return self.request("POST", "/api/cart/discount", json={"user_id": self.user_id, "discount_code": discount_code})

    def create_order(self) -> requests.Response:
        return self.request("POST", "/api/orders", json={"user_id": self.user_id})

    def pay(self, order_id: int, payment: dict) -> requests.Response:
        body = {"order_id": order_id, **payment}
        return self.request("POST", "/api/payments", json=body)
