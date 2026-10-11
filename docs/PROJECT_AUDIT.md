# Project Audit — E-Commerce Checkout Automation Framework

Audit date: 2026-10-11. Baseline: `main` at `68d79f5`. Changes are on the `interview-demo` branch.

## What the Repository Contains

Two distinct things:

1. **System under test (SUT)** — `app/`: a FastAPI "QA Shop" with Jinja2 pages and a REST API,
   backed by SQLite (`database/schema.sql`, `seed_data.sql`, `reset_database.py`).
2. **Automation framework** — `pages/`, `tests/`, `utilities/`, `postman/`, `docs/`: Playwright
   page objects and Pytest tests that check the SUT through its UI, its REST API and its database.

## Architecture

| Layer | Files | Notes |
| --- | --- | --- |
| Tests | `tests/ui/test_checkout_ui.py` (6), `tests/api/test_api_checkout.py` (3), `tests/integration/test_cross_layer_validation.py` (2) | Markers `ui`, `api`, `integration` in `pytest.ini` |
| Fixtures | `tests/conftest.py` | `app_server` (autouse: reset DB, start app as subprocess, poll `/login`, stop after test), `base_url`, `api_client`, `db_client`, `authenticated_page`, failure-screenshot hook |
| Page objects | `pages/*.py` (7 classes) | Locators via `get_by_test_id` (`data-testid`); actions + `expect_*` assertion helpers |
| API layer | `utilities/api_client.py` | `requests` wrapper; stores `user_id` after login |
| DB layer | `utilities/database_client.py` | Parameterized `SELECT`s returning dicts |
| Test oracle | `utilities/price_calculator.py` | Independent copy of the pricing formula, used to compute expected totals |
| Config/data | `utilities/config_reader.py`, `tests/test_data/test_data.py` | URLs, users, product IDs, test cards |
| Reporting | `pytest.ini` addopts, `utilities/logger.py`, `utilities/screenshots.py` | HTML (pytest-html), JUnit XML, log file, screenshot on failure |
| API collection | `postman/ecommerce_collection.json`, `local_environment.json` | 7 folders |
| QA docs | `docs/test_plan.md`, `test_cases.md`, `sql_validation_queries.md`, `framework_architecture.md`, `jira/` | |

## SUT Business Rules (from `app/app.py` and `app/services/pricing.py`)

- Login: email + password compared to `users.password_hash` (plain text in the seed data).
- Tax = 8% of subtotal; `SAVE10` discount = 10% of subtotal; final = subtotal + tax − discount.
  Money rounded with `Decimal(...).quantize(Decimal("0.01"), ROUND_HALF_UP)`.
- Add to cart: quantity ≥ 1; product must exist (404); stock 0 → 409; cart quantity > stock → 409.
- Checkout: empty cart → 400; all address fields required.
- Payment: all fields required; 16-digit card; 3-digit CVV; `MM/YY` shape.
  `4111111111111111` → SUCCESS / order PAID / stock reduced / cart cleared;
  `4000000000000002` → DECLINED / order PAYMENT_DECLINED; any other card → 400.
- Only the last four card digits are stored.

## Baseline Results (before any change)

`python -m pytest` on a clean install: **11 errors, 0 passed**. Every test failed in the
`app_server` fixture with "FastAPI application did not start". Running `python app/app.py`
directly showed `ModuleNotFoundError: No module named 'itsdangerous'`.

## Defects Found

### In the framework / project setup (fixed)

| # | Problem | Fix |
| --- | --- | --- |
| F1 | `itsdangerous` (needed by `SessionMiddleware`) missing from `requirements.txt`; `jinja2` only present through pytest-html | Added both (`d5e11ed`). Suite then: 11 passed |
| F3 | Flaky UI test: CI run [38141086452](https://github.com/ayushgupta2056/E-commerce-Checkout-Automation/actions/runs/38141086452) failed `test_complete_checkout_with_discount_and_order_history` with `assert 0.0 == 15.5`. `CartPage` clicked with `no_wait_after=True`, returning before the cart page reloaded; `amount()` then read the old totals | `CartPage` waits for the form-submit navigation with `expect_navigation()` (`b6e353b`). 3 local + 3 CI runs green afterwards |
| F2 | Postman collection failed 4/19 assertions when run with Newman: "Remove Cart Item" emptied the cart, so "Create Order" returned 400 and the payment requests cascaded to 422/500 | Re-add an item before checkout; separate order for the declined-payment check; stronger assertions (`f10bb3a`). Now 26/26 assertions pass |

### In the application under test (open, documented, `xfail` tests)

| ID | Defect | Evidence |
| --- | --- | --- |
| DEFECT-004 | Paying an already PAID order succeeds again: second `payments` row, stock decremented twice (stock 5 → buy 2 → 1) | `process_payment()` never checks `order_status` |
| DEFECT-005 | `13/30`, `ab/cd`, expired `01/20` accepted as expiry dates | `validate_card()` only checks length 5 and `/` |
| DEFECT-006 | `{"product_id": "abc"}` → 500 | `int(...)` `ValueError` reaches the generic handler |

These were deliberately **not fixed** in the SUT: the repository's purpose is to test the app,
and the defects are now caught by the framework.

## Changes Made for Deployment and Demo

- App creates the database on startup if missing (previously only in `if __name__ == "__main__"`).
- `SECRET_KEY` from environment; `DEMO_MODE=1` banner, test-data hint on the login page, `POST /demo/reset`.
- `TARGET_BASE_URL` lets UI/API tests run against a deployed instance; DB tests skip there.
- `render.yaml`, `.github/workflows/qa-tests.yml`, `tools/build_dashboard.py`.

## Deployment Risks

- Render free plan: ephemeral filesystem, spin-down after ~15 min idle, cold start up to ~1 min.
- One shared demo user; the reset button affects everyone.
- `/demo/reset` is public on the demo. It only restores seed data, but would not exist in production.

## Security Observations (SUT)

| Area | Observation |
| --- | --- |
| Passwords | Stored and compared in plain text (`password_hash == password`) |
| API authorization | `user_id` comes from the request body/query; any caller can act as any user (IDOR) |
| Sessions | Signed cookie via `SessionMiddleware`; secret now from env on the deployment |
| SQL | All queries parameterized |
| Card data | Only last four digits stored; full number and CVV never persisted |
| CSRF | No tokens on HTML forms |

## Framework Quality Observations

Strengths: page objects with stable `data-testid` locators; separate UI/API/DB clients;
independent price oracle; cross-layer integration tests; per-test DB reset for isolation;
failure screenshots; HTML + JUnit reports; negative scenarios across all layers.

Weaknesses worth knowing:
- Page-object clicks use `force=True` (and outside `CartPage`, `no_wait_after=True`), which skips
  actionability checks; waiting relies on the next `expect(...)`. This caused one real flaky failure (F3).
- `ProductDetailsPage.add_to_cart` swallows a `TimeoutError` waiting for `/cart` so the same
  method works for success and error cases.
- Several tests cover many scenarios each (e.g. the empty-cart/invalid-discount/payment-errors test),
  so one early failure hides later checks.
- The app is started and stopped for **every** test (function-scoped autouse fixture), which is slow
  (~95 s locally vs ~30 s in CI).
- No `@pytest.mark.parametrize` in the original tests.
- `utilities/config_reader.py` and `tests/test_data/test_data.py` duplicate test data.

## Resume Claims vs Evidence

| Claim | Evidence | Verdict |
| --- | --- | --- |
| E2E framework with Python + Playwright for login, search, cart, checkout, payment, confirmation | `tests/ui/test_checkout_ui.py::test_complete_checkout_with_discount_and_order_history` and page objects | Supported |
| Validations of prices, quantities, taxes, discounts, totals across UI, API and DB | `test_cart_totals_match_ui_api_and_database`, `test_order_and_payment_match_ui_api_and_database`, `price_calculator.py` | Supported |
| Negative scenarios: invalid login, empty carts, unavailable products, incorrect payment details, failed API responses | `test_invalid_login_...`, `test_empty_cart_checkout_...`, `test_out_of_stock_...`, `/api/simulate-error` test | Supported |
| Postman for REST API validation | `postman/` collection with test scripts | Collection exists, but **as committed it failed 4 assertions** when executed; fixed today. Be careful claiming it was run regularly |
| SQL queries to verify order, payment and customer data | `database_client.py`, integration tests query `orders`, `order_items`, `payments`, `carts`, `cart_items` | Order/payment: supported. **Customer (`users`) table is not queried by any test** — only listed in `docs/sql_validation_queries.md` |
| Jira | `docs/jira/*.md` in Jira format | Markdown templates; DEFECT-001..003 are labelled "sample documentation only". No evidence of a real Jira project |
