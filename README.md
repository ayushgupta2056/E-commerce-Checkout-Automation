# E-Commerce Checkout Automation Framework

[![QA Tests](https://github.com/ayushgupta2056/E-commerce-Checkout-Automation/actions/workflows/qa-tests.yml/badge.svg?branch=interview-demo)](https://github.com/ayushgupta2056/E-commerce-Checkout-Automation/actions/workflows/qa-tests.yml)

A Python + Playwright + Pytest test automation framework, together with the small
FastAPI shop ("QA Shop") it tests.

| | Link |
| --- | --- |
| Application under test (live) | https://qa-shop-checkout-demo.onrender.com |
| Latest test results dashboard | https://ayushgupta2056.github.io/E-commerce-Checkout-Automation/ |
| Same suite run against the live deployment | https://ayushgupta2056.github.io/E-commerce-Checkout-Automation/live/ |
| CI runs | https://github.com/ayushgupta2056/E-commerce-Checkout-Automation/actions/workflows/qa-tests.yml |

The live app is on Render's free plan: the first request after about 15 minutes of
inactivity can take up to a minute while it wakes up. Payments are simulated; only
the published test card numbers below are accepted and only the last four digits are stored.

## Two Parts of This Repository

**1. The system under test — `app/`, `database/`**
A FastAPI + SQLite shop with server-rendered pages (login, product search, cart,
`SAVE10` discount, 8% tax, checkout, simulated payment, order confirmation and history)
and a JSON REST API (`/api/...`) for the same operations. It exists so the framework
has something realistic to test.

**2. The automation framework — `pages/`, `tests/`, `utilities/`, `postman/`, `docs/`**
The main work. Playwright page objects, Pytest UI/API/integration tests, a requests-based
API client, a SQLite validation client, an independent price calculator used as the test
oracle, failure screenshots, HTML/JUnit reports, a Postman collection, and Jira-style
defect reports.

```text
                 ┌──────────────── tests/ (Pytest) ────────────────┐
                 │  ui/            api/              integration/  │
                 └───┬───────────────┬───────────────────┬─────────┘
                     │               │                   │
          pages/ (Page Objects)  utilities/api_client  utilities/database_client
                     │               │                   │
              Playwright Chromium   requests            sqlite3 (SELECT ... WHERE x = ?)
                     │               │                   │
                     ▼               ▼                   ▼
              ┌────────── QA Shop: FastAPI app/app.py ──────────┐
              │  HTML pages (Jinja2)    REST API /api/*          │──▶ database/ecommerce.db
              └──────────────────────────────────────────────────┘
```

## Technologies Used

- Python 3.11+
- FastAPI
- Uvicorn
- Playwright for Python
- Pytest
- Requests
- SQLite
- Postman
- HTML/CSS

## Features Tested

- Login
- Product search and details
- Cart add, update, remove
- Inventory validation
- Checkout validation
- `SAVE10` discount
- Tax, discount, subtotal, and final total calculations
- Simulated successful and declined payments
- Order confirmation and order history
- API status codes and response bodies
- SQL validation across cart, order, and payment tables

## Folder Structure

```text
ecommerce-checkout-automation/
|-- app/
|   |-- templates/
|   |-- static/
|   |-- services/
|   |-- app.py
|   `-- config.py
|-- database/
|   |-- schema.sql
|   |-- seed_data.sql
|   `-- reset_database.py
|-- docs/
|   |-- jira/
|   |-- test_plan.md
|   |-- test_cases.md
|   |-- regression_summary.md
|   |-- sql_validation_queries.md
|   `-- framework_architecture.md
|-- pages/
|-- postman/
|-- reports/
|-- tests/
|   |-- ui/
|   |-- api/
|   `-- integration/
|-- tools/
|   `-- build_dashboard.py
|-- utilities/
|-- .github/workflows/qa-tests.yml
|-- render.yaml
|-- requirements.txt
|-- pytest.ini
|-- .gitignore
|-- LICENSE
`-- README.md
```

## Prerequisites

- Windows 10 or Windows 11
- PowerShell
- VS Code
- Python 3.11 or newer

## Installation

```powershell
cd ecommerce-checkout-automation
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Initialize the Database

```powershell
python database/reset_database.py
```

## Start the FastAPI Application

```powershell
python app/app.py
```

Open the app at:

```text
http://127.0.0.1:5000
```

## Run Tests

The pytest fixtures can start the FastAPI app automatically for test execution. You can also keep the app running in another PowerShell window.

```powershell
python -m pytest
python -m pytest tests/ui
python -m pytest tests/api
python -m pytest tests/integration
python -m pytest --html=reports/report.html --self-contained-html
```

## Running Against the Deployed Demo

```powershell
$env:TARGET_BASE_URL = "https://qa-shop-checkout-demo.onrender.com"
python -m pytest
```

With `TARGET_BASE_URL` set, `conftest.py` does not start a local server; it resets the
demo data through `POST /demo/reset` before each test. UI and API tests run normally and
the database tests are skipped, because the remote SQLite file is not reachable.

## Continuous Integration

`.github/workflows/qa-tests.yml` runs on every push and on demand:

1. Installs dependencies and Playwright Chromium on `ubuntu-latest`.
2. Runs Pytest with `--tracing on --video on --screenshot on`.
3. Runs the Postman collection with Newman.
4. Builds a results dashboard (`tools/build_dashboard.py`) from `reports/junit.xml`,
   the Newman JUnit file and the Playwright artifacts, and publishes it to GitHub Pages.

A manual run with `target = live` runs the same suite against the Render deployment and
publishes it under `/live/`. Only users with write access to the repository can start runs.

## Known Defects

Exploratory testing on 2026-10-11 found three defects in the application under test.
Each has a Jira-style report in `docs/jira/` and a strict `xfail` test in
`tests/api/test_api_known_defects.py` that asserts the correct behaviour, so the
suite flags the test as soon as a fix lands.

| ID | Defect | Severity |
| --- | --- | --- |
| DEFECT-004 | A PAID order can be paid again: second payment row, stock reduced twice | Critical |
| DEFECT-005 | Expiration date is not validated (`13/30`, `ab/cd`, expired `01/20` accepted) | Major |
| DEFECT-006 | Non-numeric `product_id` in the cart API returns 500 instead of 400 | Minor |

DEFECT-001 to 003 are example reports written with the original project (marked
"sample documentation only").

## Reports

Pytest writes:

- Console output
- HTML report: `reports/report.html`
- JUnit XML report: `reports/junit.xml`
- Failure screenshots: `reports/screenshots/`
- Test log: `reports/test_run.log`
- With `--tracing on --video on --screenshot on --output test-results`: a Playwright
  trace (`trace.zip`, open with `playwright show-trace` or trace.playwright.dev), a video
  and a final screenshot for each browser test
- `python tools/build_dashboard.py --out site` builds the results dashboard locally

## Test Credentials

Valid user:

```text
Email: testuser@example.com
Password: Test@123
```

Invalid user:

```text
Email: invalid@example.com
Password: WrongPassword
```

## Payment Test Data

Successful payment:

```text
Card number: 4111111111111111
Expiration date: 12/30
CVV: 123
```

Declined payment:

```text
Card number: 4000000000000002
Expiration date: 12/30
CVV: 123
```

Only the last four card digits are stored in the database.

## Sample SQL Queries

```sql
SELECT * FROM users WHERE email = ?;
SELECT * FROM products WHERE product_id = ?;
SELECT * FROM orders WHERE order_id = ?;
SELECT * FROM order_items WHERE order_id = ?;
SELECT * FROM payments WHERE order_id = ?;
```

## Postman Usage

1. Import `postman/ecommerce_collection.json`.
2. Import `postman/local_environment.json`.
3. Select the `E-Commerce Checkout Local` environment.
4. Start the FastAPI app.
5. Run the requests in order, starting with Authentication.

## Known Limitations

- Password storage is simplified for a local QA demo.
- The app is not production hardened.
- Payment processing is simulated.
- Browser coverage is focused on Chromium.
- The public demo runs on Render's free plan, which has no persistent disk: the SQLite
  database is recreated from `schema.sql` and `seed_data.sql` whenever the service restarts.
- The demo has one shared test user, so concurrent visitors share a cart.
- The REST API identifies the user by a `user_id` in the request, without a token.
  That keeps API tests simple but would be an authorization hole in a real shop.
- UI tests click with `force=True`, which skips Playwright's actionability checks.

## Future Improvements

- Add password hashing.
- Fix DEFECT-004 to 006 and remove their `xfail` markers.
- Add more edge cases around product inventory updates.
- Start the app once per session instead of once per test to speed up the suite.
- Split the larger multi-scenario tests into smaller parametrized tests.
