# Framework Architecture

The project uses a beginner-friendly layered structure.

## Application Layer

- `app/app.py` contains FastAPI UI routes and REST API routes.
- `app/templates/` contains HTML pages.
- `app/static/` contains CSS.
- `app/services/pricing.py` centralizes subtotal, tax, discount, and final total calculations.

## Database Layer

- `database/schema.sql` defines SQLite tables.
- `database/seed_data.sql` inserts deterministic users and products.
- `database/reset_database.py` recreates the database before local runs and automated tests.

## Automation Layer

- `pages/` contains Playwright page objects.
- `tests/ui/` contains UI workflows.
- `tests/api/` contains REST API tests.
- `tests/integration/` validates UI, API, and database consistency.
- `utilities/` contains API, database, config, screenshot, logging, and price helper modules.

## Reporting

Pytest writes HTML and JUnit reports to `reports/`. Failed UI tests save screenshots to `reports/screenshots/`.
