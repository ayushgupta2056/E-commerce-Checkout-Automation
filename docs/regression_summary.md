# Regression Test Summary

## Execution Details

- Test execution date: 2026-10-11
- Environments:
  - GitHub Actions `ubuntu-latest`, Python 3.12, Chromium, app started inside the runner
  - GitHub Actions against the live Render deployment (https://qa-shop-checkout-demo.onrender.com)
  - Windows 11, Python 3.12.10, local app
- Build/version: `interview-demo` branch

## Results

| Metric | App in runner | Live deployment |
| --- | ---: | ---: |
| Total tests | 16 | 16 |
| Passed tests | 11 | 9 |
| Failed tests | 0 | 0 |
| Known-defect tests (xfail) | 5 | 5 |
| Skipped tests (DB access needed) | 0 | 2 |
| Postman assertions (Newman) | 26/26 passed | 26/26 passed |
| Open defects | 3 (DEFECT-004, 005, 006) | same |

Latest results: https://ayushgupta2056.github.io/E-commerce-Checkout-Automation/
Full details: `docs/TEST_REPORT.md`.

## Overall Recommendation

All critical checkout paths pass in the UI, API and database layers. Not ready for release
until DEFECT-004 (an order can be paid twice, reducing stock twice) is fixed; DEFECT-005
and DEFECT-006 should be fixed in the same cycle.
