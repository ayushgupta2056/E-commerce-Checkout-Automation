# DEFECT-003

## Title
Declined payment incorrectly creates a successful order

## Environment
Windows 11, Chrome/Chromium, FastAPI local server, SQLite

## Preconditions
- User has a product in the cart
- User has completed checkout details

## Steps to Reproduce
1. Open the payment page.
2. Enter card number `4000000000000002`.
3. Submit payment.
4. Query the order and payment records.

## Expected Result
Payment status is `DECLINED` and order status is `PAYMENT_DECLINED`.

## Actual Result
Example documentation defect: order status is incorrectly saved as `PAID`.

## Severity
Critical

## Priority
P1

## Status
Closed - sample documentation only

## Screenshot Placeholder
`reports/screenshots/DEFECT-003.png`

## Evidence
`payments.payment_status` and `orders.order_status` show inconsistent successful values after declined payment.
