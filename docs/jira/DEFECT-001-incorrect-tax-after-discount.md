# DEFECT-001

## Title
Incorrect tax calculation after applying discount

## Environment
Windows 11, Chrome/Chromium, FastAPI local server, SQLite

## Preconditions
- User is logged in as `testuser@example.com`
- Cart contains at least one product

## Steps to Reproduce
1. Add a product to the cart.
2. Apply discount code `SAVE10`.
3. Compare subtotal, tax, discount, and final total in UI, API, and database.

## Expected Result
Tax is 8% of the subtotal. Discount is 10% of the subtotal. Final total equals subtotal plus tax minus discount.

## Actual Result
Example documentation defect: tax is calculated after discount is subtracted.

## Severity
High

## Priority
P1

## Status
Closed - sample documentation only

## Screenshot Placeholder
`reports/screenshots/DEFECT-001.png`

## Evidence
API response and `orders` table values do not match the expected pricing formula.
