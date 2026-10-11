# DEFECT-005

## Title
Payment accepts invalid or expired expiration dates

## Found
2026-10-11, during interview-demo preparation.
Automated as `tests/api/test_api_known_defects.py::test_invalid_or_expired_card_is_rejected` (xfail, strict).

## Steps to Reproduce
1. Create an order with one item.
2. `POST /api/payments` with card `4111111111111111`, CVV `123` and expiration `13/30`, `ab/cd` or `01/20`.

## Expected Result
HTTP 400 with a validation message.

## Actual Result
HTTP 200, `payment_status` `SUCCESS`.

## Root Cause
`validate_card()` only checks that the value has 5 characters and contains `/`.

## Severity / Priority
Major / P2

## Status
Open
