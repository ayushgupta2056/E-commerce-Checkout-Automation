# E-Commerce Checkout Automation Framework

A complete beginner-to-intermediate QA automation portfolio project that tests a local e-commerce checkout workflow across the UI, REST API, and SQLite database.

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
|-- utilities/
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

## Reports

Pytest writes:

- Console output
- HTML report: `reports/report.html`
- JUnit XML report: `reports/junit.xml`
- Failure screenshots: `reports/screenshots/`
- Test log: `reports/test_run.log`

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
- No Docker or cloud deployment is included.

## Future Improvements

- Add password hashing.
- Add trace capture for failed Playwright tests.
- Add more edge cases around product inventory updates.
- Add a GitHub Actions workflow after the project is uploaded.
