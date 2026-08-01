# Test Plan

## Scope

This project validates a local e-commerce checkout workflow across UI, REST API, and SQLite database layers.

## Features In Scope

- Login and invalid authentication
- Product listing, search, and details
- Cart add, update, remove, and inventory limits
- Checkout validation
- Discount calculation with `SAVE10`
- Simulated payment success and decline
- Order confirmation and order history
- API response codes and JSON fields
- Database validation for cart, order, and payment records

## Out of Scope

- Real payment processing
- Email notifications
- Production security hardening
- Cloud deployment
- Cross-browser certification beyond Chromium

## Test Types

- UI tests with Playwright and Pytest
- REST API tests with Python Requests
- SQLite validation tests with parameterized SQL
- Cross-layer integration tests

## Entry Criteria

- Python dependencies are installed
- Playwright Chromium browser is installed
- Database reset script completes successfully
- FastAPI app starts on `http://127.0.0.1:5000`

## Exit Criteria

- Critical checkout paths pass
- Negative tests validate clear errors
- Reports are generated in `reports/`
- No known blocker defects remain open
