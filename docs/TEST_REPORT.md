# Test Report — E-Commerce Checkout Automation

All results below come from real executions on 2026-10-11. Live, regenerated results:
https://ayushgupta2056.github.io/E-commerce-Checkout-Automation/

## Summary

| Run | Target | Result |
| --- | --- | --- |
| Original `main` (`68d79f5`), clean install, Windows 11 | Local app | **0 passed, 11 errors** (app could not start: missing `itsdangerous`) |
| After dependency fix (`d5e11ed`), Windows 11 | Local app | **11 passed** in 56 s |
| `interview-demo`, Windows 11, with trace/video/screenshot | Local app | **11 passed, 5 xfailed** in 97 s |
| GitHub Actions run #1 (`0dfc531`, [link](https://github.com/ayushgupta2056/E-commerce-Checkout-Automation/actions/runs/38139917711)) | App started inside the runner | **11 passed, 5 xfailed** in 28.9 s |
| GitHub Actions run #2 (`workflow_dispatch`, [link](https://github.com/ayushgupta2056/E-commerce-Checkout-Automation/actions/runs/38140467984)) | **Live Render deployment** | **9 passed, 2 skipped, 5 xfailed** in 34.3 s (DB tests skip remotely by design) |
| GitHub Actions run #3 (`7f0c838`, [link](https://github.com/ayushgupta2056/E-commerce-Checkout-Automation/actions/runs/38140814793)) | App inside runner | **11 passed, 5 xfailed**; Newman **22 requests, 26/26 assertions** |
| GitHub Actions run #4 (`460fe01`, push, [link](https://github.com/ayushgupta2056/E-commerce-Checkout-Automation/actions/runs/38141086452)) | App inside runner | **1 failed**, 10 passed, 5 xfailed — flaky race in `CartPage` (`assert 0.0 == 15.5`) |
| Runs on fix `b6e353b` (push + 2 manual) | App inside runner ×2, live ×1 | 11 passed / 5 xfailed (×2); 9 passed / 2 skipped / 5 xfailed (live) |
| Newman, original collection | Live deployment | 19 requests, **4 assertions failed** (request-order bug, fixed) |
| Newman, fixed collection | Live deployment | 22 requests, **26/26 assertions passed** |

XFAIL = test asserting correct behaviour for an open defect (DEFECT-004..006); expected to fail until fixed.

## Automated Tests

| Test | Layer | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| test_complete_checkout_with_discount_and_order_history | UI | Login → search "Keyboard" → add keyboard ×1, mouse ×2 → update mouse to 3 → SAVE10 → totals equal oracle → checkout → pay 4111… → "PAID" → order in history | As expected | PASS |
| test_cart_update_and_remove_item | UI | Hub qty 2 → line total $99.00 → remove → empty-cart message | As expected | PASS |
| test_invalid_login_and_empty_login_show_errors | UI, negative | "Invalid email or password." then "Email and password are required." | As expected | PASS |
| test_product_search_no_results | UI, negative | "No products found." | As expected | PASS |
| test_out_of_stock_and_over_stock_are_blocked | UI, negative | Laptop Stand (stock 0) → "out of stock"; headphones ×6 (stock 5) → "exceeds available stock" | As expected | PASS |
| test_empty_cart_checkout_invalid_discount_checkout_and_payment_errors | UI, negative | Empty-cart checkout blocked; BADCODE rejected; missing address; empty card fields; 3-digit card; declined card | All six errors shown | PASS |
| test_login_products_and_product_errors | API | Login 200 / invalid 401; products list; search; product by ID; 404 for missing | As expected | PASS |
| test_cart_discount_order_and_successful_payment | API | Add/update cart, SAVE10 totals match oracle, order 201, payment SUCCESS, last four "1111", order PAID | As expected | PASS |
| test_cart_negative_paths_declined_payment_and_failed_response | API, negative | 409 out of stock; 409 over stock; 400 bad code; 400 empty-cart order; DECLINED; 404 order; 500 simulated failure | As expected | PASS |
| test_cart_totals_match_ui_api_and_database | Integration | UI totals == API totals; API items == `cart_items` rows (SQL) | As expected | PASS (SKIP on live target) |
| test_order_and_payment_match_ui_api_and_database | Integration | UI order ID → API order == `orders` row; total == `payments.amount`; `order_items` product; payment SUCCESS, "1111" | As expected | PASS (SKIP on live target) |
| test_paid_order_cannot_be_paid_twice | API, defect | Second payment rejected; stock 3 | 200 SUCCESS; stock 1 | XFAIL (DEFECT-004) |
| test_invalid_or_expired_card_is_rejected[13/30] | API, defect | 400 | 200 SUCCESS | XFAIL (DEFECT-005) |
| test_invalid_or_expired_card_is_rejected[ab/cd] | API, defect | 400 | 200 SUCCESS | XFAIL (DEFECT-005) |
| test_invalid_or_expired_card_is_rejected[01/20] | API, defect | 400 | 200 SUCCESS | XFAIL (DEFECT-005) |
| test_non_numeric_product_id_returns_client_error | API, defect | 400 | 500 | XFAIL (DEFECT-006) |

**Totals (local / CI target):** 16 collected — 11 passed, 0 failed, 5 xfailed, 0 skipped.
**Totals (live target):** 16 collected — 9 passed, 0 failed, 5 xfailed, 2 skipped.

## Manual Checks of the Live Deployment (curl, 2026-10-11)

| Check | Expected | Actual | Status |
| --- | --- | --- | --- |
| Login page | Demo banner, test-data hint, https stylesheet | As expected | PASS |
| Invalid login | Error message | "Invalid email or password." | PASS |
| Search "Keyboard" | Product 102 only | product-card-102 | PASS |
| Keyboard ×1 + mouse ×3 + SAVE10 | 154.96 / 12.40 / 15.50 / 151.86 | Same | PASS |
| Declined card 4000…0002 | "Payment was declined." | Shown | PASS |
| Approved card 4111…1111 | Redirect to confirmation, PAID, $151.86 | Order 1, PAID, $151.86 | PASS |
| `GET /api/products/99999` | 404 | 404 | PASS |
| `GET /api/simulate-error` | 500 | 500 | PASS |
| `POST /demo/reset` | 303, stock restored | As expected | PASS |

## Evidence

Each CI run publishes: pytest-html report, JUnit XML, execution log, Newman JUnit and log,
and for every browser test a Playwright trace, video and final screenshot.
