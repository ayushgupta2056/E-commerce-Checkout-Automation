from __future__ import annotations

from pathlib import Path
import sqlite3
import sys
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from config import DATABASE_PATH, DEMO_MODE, SECRET_KEY
from services.pricing import VALID_DISCOUNT_CODE, calculate_totals, money


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="QA Shop")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.globals["demo_mode"] = DEMO_MODE


def reset_demo_database() -> None:
    sys.path.append(str(Path(__file__).resolve().parents[1] / "database"))
    from reset_database import reset_database

    reset_database()


if not Path(DATABASE_PATH).exists():
    reset_demo_database()


def get_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row else None


def render(request: Request, template: str, context: dict | None = None, status_code: int = 200) -> HTMLResponse:
    return templates.TemplateResponse(template, {"request": request, **(context or {})}, status_code=status_code)


def redirect_to(request: Request, route_name: str, status_code: int = 303, **path_params: Any) -> RedirectResponse:
    return RedirectResponse(str(request.url_for(route_name, **path_params)), status_code=status_code)


def get_user_by_email(email: str) -> sqlite3.Row | None:
    with get_db() as db:
        return db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def current_user_id(request: Request) -> int | None:
    return request.session.get("user_id")


def require_login(request: Request) -> RedirectResponse | None:
    if not current_user_id(request):
        return redirect_to(request, "login", status_code=303)
    return None


def get_or_create_cart(user_id: int) -> sqlite3.Row:
    with get_db() as db:
        cart = db.execute("SELECT * FROM carts WHERE user_id = ?", (user_id,)).fetchone()
        if cart:
            return cart
        db.execute("INSERT INTO carts (user_id) VALUES (?)", (user_id,))
        db.commit()
        return db.execute("SELECT * FROM carts WHERE user_id = ?", (user_id,)).fetchone()


def get_product(product_id: int) -> sqlite3.Row | None:
    with get_db() as db:
        return db.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()


def cart_snapshot(user_id: int) -> dict:
    cart = get_or_create_cart(user_id)
    with get_db() as db:
        rows = db.execute(
            """
            SELECT ci.cart_item_id, ci.quantity, p.product_id, p.name, p.price,
                   p.stock_quantity, p.category
            FROM cart_items ci
            JOIN products p ON p.product_id = ci.product_id
            WHERE ci.cart_id = ?
            ORDER BY p.product_id
            """,
            (cart["cart_id"],),
        ).fetchall()

    items = []
    subtotal = 0.0
    for row in rows:
        line_total = money(row["price"] * row["quantity"])
        subtotal += line_total
        items.append(
            {
                "product_id": row["product_id"],
                "name": row["name"],
                "price": money(row["price"]),
                "quantity": row["quantity"],
                "stock_quantity": row["stock_quantity"],
                "category": row["category"],
                "line_total": line_total,
            }
        )
    totals = calculate_totals(subtotal, cart["discount_code"])
    return {
        "cart_id": cart["cart_id"],
        "user_id": user_id,
        "discount_code": cart["discount_code"],
        "items": items,
        **totals,
    }


def add_cart_item(user_id: int, product_id: int, quantity: int) -> tuple[dict, int]:
    if quantity < 1:
        return {"error": "Quantity must be at least 1."}, 400
    product = get_product(product_id)
    if not product:
        return {"error": "Product not found."}, 404
    if product["stock_quantity"] == 0:
        return {"error": "Product is out of stock."}, 409

    cart = get_or_create_cart(user_id)
    with get_db() as db:
        existing = db.execute(
            "SELECT quantity FROM cart_items WHERE cart_id = ? AND product_id = ?",
            (cart["cart_id"], product_id),
        ).fetchone()
        new_quantity = quantity + (existing["quantity"] if existing else 0)
        if new_quantity > product["stock_quantity"]:
            return {"error": "Requested quantity exceeds available stock."}, 409
        if existing:
            db.execute(
                "UPDATE cart_items SET quantity = ? WHERE cart_id = ? AND product_id = ?",
                (new_quantity, cart["cart_id"], product_id),
            )
        else:
            db.execute(
                "INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (?, ?, ?)",
                (cart["cart_id"], product_id, quantity),
            )
        db.commit()
    return cart_snapshot(user_id), 200


def update_cart_item(user_id: int, product_id: int, quantity: int) -> tuple[dict, int]:
    if quantity < 1:
        return {"error": "Quantity must be at least 1."}, 400
    product = get_product(product_id)
    if not product:
        return {"error": "Product not found."}, 404
    if quantity > product["stock_quantity"]:
        return {"error": "Requested quantity exceeds available stock."}, 409
    cart = get_or_create_cart(user_id)
    with get_db() as db:
        existing = db.execute(
            "SELECT cart_item_id FROM cart_items WHERE cart_id = ? AND product_id = ?",
            (cart["cart_id"], product_id),
        ).fetchone()
        if not existing:
            return {"error": "Cart item not found."}, 404
        db.execute(
            "UPDATE cart_items SET quantity = ? WHERE cart_id = ? AND product_id = ?",
            (quantity, cart["cart_id"], product_id),
        )
        db.commit()
    return cart_snapshot(user_id), 200


def remove_cart_item(user_id: int, product_id: int) -> tuple[dict, int]:
    cart = get_or_create_cart(user_id)
    with get_db() as db:
        db.execute("DELETE FROM cart_items WHERE cart_id = ? AND product_id = ?", (cart["cart_id"], product_id))
        db.commit()
    return cart_snapshot(user_id), 200


def apply_discount(user_id: int, discount_code: str) -> tuple[dict, int]:
    if discount_code != VALID_DISCOUNT_CODE:
        return {"error": "Invalid discount code."}, 400
    cart = get_or_create_cart(user_id)
    with get_db() as db:
        db.execute("UPDATE carts SET discount_code = ? WHERE cart_id = ?", (discount_code, cart["cart_id"]))
        db.commit()
    return cart_snapshot(user_id), 200


def get_order(order_id: int) -> dict | None:
    with get_db() as db:
        order = db.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
        if not order:
            return None
        items = db.execute(
            """
            SELECT oi.order_item_id, oi.product_id, p.name, oi.quantity, oi.unit_price, oi.line_total
            FROM order_items oi
            JOIN products p ON p.product_id = oi.product_id
            WHERE oi.order_id = ?
            ORDER BY oi.product_id
            """,
            (order_id,),
        ).fetchall()
        payment = db.execute(
            "SELECT * FROM payments WHERE order_id = ? ORDER BY payment_id DESC LIMIT 1",
            (order_id,),
        ).fetchone()
    data = row_to_dict(order)
    data["items"] = [row_to_dict(item) for item in items]
    data["payment"] = row_to_dict(payment)
    return data


def create_order(user_id: int) -> tuple[dict, int]:
    snapshot = cart_snapshot(user_id)
    if not snapshot["items"]:
        return {"error": "Checkout is not allowed when the cart is empty."}, 400
    with get_db() as db:
        cursor = db.execute(
            """
            INSERT INTO orders (user_id, subtotal, tax, discount, final_total, order_status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, snapshot["subtotal"], snapshot["tax"], snapshot["discount"], snapshot["final_total"], "PENDING_PAYMENT"),
        )
        order_id = cursor.lastrowid
        for item in snapshot["items"]:
            db.execute(
                """
                INSERT INTO order_items (order_id, product_id, quantity, unit_price, line_total)
                VALUES (?, ?, ?, ?, ?)
                """,
                (order_id, item["product_id"], item["quantity"], item["price"], item["line_total"]),
            )
        db.commit()
    return get_order(order_id), 201


def validate_card(cardholder_name: str, card_number: str, expiration_date: str, cvv: str) -> str | None:
    if not cardholder_name.strip() or not card_number.strip() or not expiration_date.strip() or not cvv.strip():
        return "All payment fields are required."
    if not card_number.isdigit() or len(card_number) != 16:
        return "Card number must be 16 digits."
    if not cvv.isdigit() or len(cvv) != 3:
        return "CVV must be 3 digits."
    if "/" not in expiration_date or len(expiration_date) != 5:
        return "Expiration date must use MM/YY format."
    return None


def process_payment(order_id: int, cardholder_name: str, card_number: str, expiration_date: str, cvv: str) -> tuple[dict, int]:
    validation_error = validate_card(cardholder_name, card_number, expiration_date, cvv)
    if validation_error:
        return {"error": validation_error}, 400
    order = get_order(order_id)
    if not order:
        return {"error": "Order not found."}, 404

    if card_number == "4111111111111111":
        status = "SUCCESS"
        order_status = "PAID"
    elif card_number == "4000000000000002":
        status = "DECLINED"
        order_status = "PAYMENT_DECLINED"
    else:
        return {"error": "Unsupported test card number."}, 400

    with get_db() as db:
        db.execute(
            """
            INSERT INTO payments (order_id, amount, last_four_card_digits, payment_status)
            VALUES (?, ?, ?, ?)
            """,
            (order_id, order["final_total"], card_number[-4:], status),
        )
        db.execute("UPDATE orders SET order_status = ? WHERE order_id = ?", (order_status, order_id))
        if status == "SUCCESS":
            for item in order["items"]:
                db.execute(
                    "UPDATE products SET stock_quantity = stock_quantity - ? WHERE product_id = ?",
                    (item["quantity"], item["product_id"]),
                )
            db.execute("DELETE FROM cart_items WHERE cart_id = (SELECT cart_id FROM carts WHERE user_id = ?)", (order["user_id"],))
            db.execute("UPDATE carts SET discount_code = NULL WHERE user_id = ?", (order["user_id"],))
        db.commit()

    response = get_order(order_id)
    response["payment_status"] = status
    response["last_four_card_digits"] = card_number[-4:]
    return response, 200


async def request_json(request: Request) -> dict:
    try:
        return await request.json()
    except Exception:
        return {}


def json_response(body: dict, status_code: int = 200) -> JSONResponse:
    return JSONResponse(body, status_code=status_code)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return redirect_to(request, "products" if current_user_id(request) else "login")


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return render(request, "login.html")


@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request):
    form = await request.form()
    email = str(form.get("email", "")).strip()
    password = str(form.get("password", ""))
    if not email or not password:
        return render(request, "login.html", {"error": "Email and password are required."})
    user = get_user_by_email(email)
    if user and user["password_hash"] == password:
        request.session["user_id"] = user["user_id"]
        request.session["user_name"] = user["name"]
        get_or_create_cart(user["user_id"])
        return redirect_to(request, "products")
    return render(request, "login.html", {"error": "Invalid email or password."})


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return redirect_to(request, "login")


@app.get("/products", response_class=HTMLResponse)
async def products(request: Request, q: str = ""):
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect
    query = q.strip()
    with get_db() as db:
        if query:
            rows = db.execute(
                "SELECT * FROM products WHERE name LIKE ? OR category LIKE ? ORDER BY product_id",
                (f"%{query}%", f"%{query}%"),
            ).fetchall()
        else:
            rows = db.execute("SELECT * FROM products ORDER BY product_id").fetchall()
    return render(request, "products.html", {"products": rows, "query": query})


@app.get("/products/{product_id}", response_class=HTMLResponse)
async def product_details(request: Request, product_id: int):
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect
    product = get_product(product_id)
    if not product:
        return render(request, "error.html", {"message": "Product not found."}, status_code=404)
    return render(request, "product_details.html", {"product": product})


@app.post("/cart/add", response_class=HTMLResponse)
async def ui_add_cart(request: Request):
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect
    form = await request.form()
    product_id = int(form["product_id"])
    quantity = int(form.get("quantity", 1))
    response, status = add_cart_item(current_user_id(request), product_id, quantity)
    if status != 200:
        return render(request, "product_details.html", {"product": get_product(product_id), "error": response["error"]}, status_code=status)
    return redirect_to(request, "cart")


@app.get("/cart", response_class=HTMLResponse)
async def cart(request: Request):
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect
    return render(request, "cart.html", {"cart": cart_snapshot(current_user_id(request))})


@app.post("/cart", response_class=HTMLResponse)
async def cart_post(request: Request):
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect
    error = None
    form = await request.form()
    action = form.get("action")
    product_id = int(form.get("product_id", 0))
    if action == "update":
        response, status = update_cart_item(current_user_id(request), product_id, int(form["quantity"]))
        if status != 200:
            error = response["error"]
    elif action == "remove":
        remove_cart_item(current_user_id(request), product_id)
    elif action == "discount":
        response, status = apply_discount(current_user_id(request), str(form.get("discount_code", "")).strip())
        if status != 200:
            error = response["error"]
    return render(request, "cart.html", {"cart": cart_snapshot(current_user_id(request)), "error": error})


@app.get("/checkout", response_class=HTMLResponse)
async def checkout(request: Request):
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect
    snapshot = cart_snapshot(current_user_id(request))
    if not snapshot["items"]:
        return render(request, "cart.html", {"cart": snapshot, "error": "Checkout is not allowed when the cart is empty."}, status_code=400)
    return render(request, "checkout.html", {"cart": snapshot})


@app.post("/checkout", response_class=HTMLResponse)
async def checkout_post(request: Request):
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect
    snapshot = cart_snapshot(current_user_id(request))
    form = await request.form()
    required = ["full_name", "address", "city", "zip_code"]
    if any(not str(form.get(field, "")).strip() for field in required):
        return render(request, "checkout.html", {"cart": snapshot, "error": "All checkout fields are required."})
    order, _ = create_order(current_user_id(request))
    request.session["order_id"] = order["order_id"]
    return redirect_to(request, "payment")


@app.get("/payment", response_class=HTMLResponse)
async def payment(request: Request):
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect
    order_id = request.session.get("order_id")
    if not order_id:
        return redirect_to(request, "checkout")
    return render(request, "payment.html", {"order": get_order(order_id)})


@app.post("/payment", response_class=HTMLResponse)
async def payment_post(request: Request):
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect
    order_id = request.session.get("order_id")
    if not order_id:
        return redirect_to(request, "checkout")
    form = await request.form()
    response, status = process_payment(
        order_id,
        str(form.get("cardholder_name", "")),
        str(form.get("card_number", "")),
        str(form.get("expiration_date", "")),
        str(form.get("cvv", "")),
    )
    if status == 200 and response["payment_status"] == "SUCCESS":
        return redirect_to(request, "order_confirmation", order_id=order_id)
    error = response.get("error") or "Payment was declined."
    return render(request, "payment.html", {"order": get_order(order_id), "error": error})


@app.get("/orders/{order_id}", response_class=HTMLResponse)
async def order_confirmation(request: Request, order_id: int):
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect
    order = get_order(order_id)
    if not order or order["user_id"] != current_user_id(request):
        return render(request, "error.html", {"message": "Order not found."}, status_code=404)
    return render(request, "order_confirmation.html", {"order": order})


@app.get("/order-history", response_class=HTMLResponse)
async def order_history(request: Request):
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect
    with get_db() as db:
        orders = db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY order_id DESC",
            (current_user_id(request),),
        ).fetchall()
    return render(request, "order_history.html", {"orders": orders})


@app.post("/api/login")
async def api_login(request: Request):
    data = await request_json(request)
    user = get_user_by_email(data.get("email", ""))
    if user and user["password_hash"] == data.get("password", ""):
        get_or_create_cart(user["user_id"])
        return json_response({"user_id": user["user_id"], "name": user["name"], "email": user["email"]})
    return json_response({"error": "Invalid email or password."}, 401)


@app.get("/api/products")
async def api_products(search: str = ""):
    query = search.strip()
    with get_db() as db:
        if query:
            rows = db.execute(
                "SELECT * FROM products WHERE name LIKE ? OR category LIKE ? ORDER BY product_id",
                (f"%{query}%", f"%{query}%"),
            ).fetchall()
        else:
            rows = db.execute("SELECT * FROM products ORDER BY product_id").fetchall()
    return json_response({"products": [row_to_dict(row) for row in rows]})


@app.get("/api/products/{product_id}")
async def api_product(product_id: int):
    product = get_product(product_id)
    if not product:
        return json_response({"error": "Product not found."}, 404)
    return json_response(row_to_dict(product))


async def api_user_id(request: Request) -> int | None:
    data = {}
    if request.method in {"POST", "PUT", "PATCH"}:
        data = await request_json(request)
    value = data.get("user_id") or request.query_params.get("user_id")
    return int(value) if value else None


@app.get("/api/cart")
async def api_view_cart(request: Request):
    user_id = await api_user_id(request)
    if not user_id:
        return json_response({"error": "user_id is required."}, 401)
    return json_response(cart_snapshot(user_id))


@app.post("/api/cart/items")
async def api_add_item(request: Request):
    data = await request_json(request)
    user_id = data.get("user_id")
    if not user_id:
        return json_response({"error": "user_id is required."}, 401)
    response, status = add_cart_item(int(user_id), int(data.get("product_id", 0)), int(data.get("quantity", 1)))
    return json_response(response, status)


@app.put("/api/cart/items/{product_id}")
async def api_update_item(request: Request, product_id: int):
    data = await request_json(request)
    user_id = data.get("user_id")
    if not user_id:
        return json_response({"error": "user_id is required."}, 401)
    response, status = update_cart_item(int(user_id), product_id, int(data.get("quantity", 1)))
    return json_response(response, status)


@app.delete("/api/cart/items/{product_id}")
async def api_remove_item(request: Request, product_id: int):
    user_id = await api_user_id(request)
    if not user_id:
        return json_response({"error": "user_id is required."}, 401)
    response, status = remove_cart_item(user_id, product_id)
    return json_response(response, status)


@app.post("/api/cart/discount")
async def api_discount(request: Request):
    data = await request_json(request)
    user_id = data.get("user_id")
    if not user_id:
        return json_response({"error": "user_id is required."}, 401)
    response, status = apply_discount(int(user_id), data.get("discount_code", ""))
    return json_response(response, status)


@app.post("/api/orders")
async def api_create_order(request: Request):
    data = await request_json(request)
    user_id = data.get("user_id")
    if not user_id:
        return json_response({"error": "user_id is required."}, 401)
    response, status = create_order(int(user_id))
    return json_response(response, status)


@app.get("/api/orders/{order_id}")
async def api_get_order(order_id: int):
    order = get_order(order_id)
    if not order:
        return json_response({"error": "Order not found."}, 404)
    return json_response(order)


@app.post("/api/payments")
async def api_payment(request: Request):
    data = await request_json(request)
    response, status = process_payment(
        int(data.get("order_id", 0)),
        data.get("cardholder_name", ""),
        data.get("card_number", ""),
        data.get("expiration_date", ""),
        data.get("cvv", ""),
    )
    return json_response(response, status)


@app.get("/api/simulate-error")
async def api_simulate_error():
    return json_response({"error": "Controlled failure for negative API testing."}, 500)


@app.post("/demo/reset")
async def demo_reset(request: Request):
    if not DEMO_MODE:
        return json_response({"error": "Not found."}, 404)
    reset_demo_database()
    request.session.clear()
    return redirect_to(request, "login")


@app.exception_handler(Exception)
async def server_error(request: Request, exc: Exception):
    return json_response({"error": "Internal server error."}, 500)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")
