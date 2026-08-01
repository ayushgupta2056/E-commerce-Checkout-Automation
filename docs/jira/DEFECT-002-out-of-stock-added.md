# DEFECT-002

## Title
Out-of-stock product can be added to the cart

## Environment
Windows 11, Chrome/Chromium, FastAPI local server, SQLite

## Preconditions
- User is logged in as `testuser@example.com`
- Product `105` has stock quantity `0`

## Steps to Reproduce
1. Open the product details page for Laptop Stand.
2. Enter quantity `1`.
3. Click Add to cart.

## Expected Result
The app blocks the request and displays `Product is out of stock.`

## Actual Result
Example documentation defect: product is added to the cart.

## Severity
High

## Priority
P1

## Status
Closed - sample documentation only

## Screenshot Placeholder
`reports/screenshots/DEFECT-002.png`

## Evidence
Unexpected row appears in `cart_items` for product ID `105`.
