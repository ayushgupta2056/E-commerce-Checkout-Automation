# DEFECT-004

## Title
An order that is already PAID can be paid again, creating a second payment and reducing stock twice

## Found
2026-10-11, during interview-demo preparation, by exploratory API testing.
Automated as `tests/api/test_api_known_defects.py::test_paid_order_cannot_be_paid_twice` (xfail, strict).

## Environment
FastAPI app on `interview-demo` branch, SQLite, Python 3.12

## Steps to Reproduce
1. `POST /api/login` as `testuser@example.com`.
2. `POST /api/cart/items` with product `104` (stock 5), quantity `2`.
3. `POST /api/orders` and note `order_id`.
4. `POST /api/payments` with card `4111111111111111` -> `SUCCESS`.
5. Repeat step 4 for the same `order_id`.

## Expected Result
The second request is rejected (HTTP 400/409). One payment row exists. Product `104` stock is `3`.

## Actual Result
The second request returns HTTP 200 `SUCCESS`, a second row is inserted into `payments`,
and product `104` stock drops to `1`.

## Root Cause
`process_payment()` in `app/app.py` does not check `orders.order_status` before charging.

## Severity / Priority
Critical / P1

## Status
Open
