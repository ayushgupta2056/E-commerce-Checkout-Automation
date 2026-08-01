# Test Cases

| ID | Area | Scenario | Expected Result |
| --- | --- | --- | --- |
| TC-UI-001 | Login | Valid user login | User lands on products page |
| TC-UI-002 | Login | Invalid user login | Error message is displayed |
| TC-UI-003 | Products | Search for existing product | Matching product appears |
| TC-UI-004 | Products | Search for missing product | No products message appears |
| TC-UI-005 | Cart | Add product to cart | Product appears in cart |
| TC-UI-006 | Cart | Update product quantity | Line total and subtotal update |
| TC-UI-007 | Cart | Remove product | Product is removed from cart |
| TC-UI-008 | Cart | Add out-of-stock product | Request is blocked |
| TC-UI-009 | Cart | Quantity greater than stock | Request is blocked |
| TC-UI-010 | Discount | Apply SAVE10 | Discount equals 10% of subtotal |
| TC-UI-011 | Discount | Apply invalid code | Error message appears |
| TC-UI-012 | Checkout | Empty cart checkout | Checkout is blocked |
| TC-UI-013 | Checkout | Missing address fields | Validation error appears |
| TC-UI-014 | Payment | Valid test card | Order is confirmed |
| TC-UI-015 | Payment | Invalid card format | Validation error appears |
| TC-UI-016 | Payment | Declined test card | Declined error appears |
| TC-API-001 | API | Login success | HTTP 200 with user fields |
| TC-API-002 | API | Login failure | HTTP 401 with error |
| TC-API-003 | API | Product not found | HTTP 404 |
| TC-API-004 | API | Controlled server failure | HTTP 500 |
| TC-INT-001 | Integration | Cart totals across UI/API/DB | Product data and totals match |
| TC-INT-002 | Integration | Order/payment across UI/API/DB | Order and payment records match |
