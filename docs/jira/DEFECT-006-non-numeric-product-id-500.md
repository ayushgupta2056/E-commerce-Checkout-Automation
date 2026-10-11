# DEFECT-006

## Title
Non-numeric `product_id` in the cart API returns HTTP 500 instead of 400

## Found
2026-10-11, during interview-demo preparation.
Automated as `tests/api/test_api_known_defects.py::test_non_numeric_product_id_returns_client_error` (xfail, strict).

## Steps to Reproduce
`POST /api/cart/items` with body `{"user_id": 1, "product_id": "abc", "quantity": 1}`.

## Expected Result
HTTP 400 with an error message.

## Actual Result
HTTP 500 `{"error": "Internal server error."}`.

## Root Cause
`int(data.get("product_id", 0))` raises `ValueError`, which reaches the generic exception handler.

## Severity / Priority
Minor / P3

## Status
Open
