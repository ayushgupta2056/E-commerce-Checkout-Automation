# SQL Validation Queries

Use parameterized queries in automation. Do not build SQL by concatenating user-provided values.

```sql
SELECT * FROM users WHERE email = ?;

SELECT * FROM products WHERE product_id = ?;

SELECT * FROM carts WHERE user_id = ?;

SELECT ci.product_id, ci.quantity, p.price
FROM cart_items ci
JOIN products p ON p.product_id = ci.product_id
WHERE ci.cart_id = ?;

SELECT * FROM orders WHERE order_id = ?;

SELECT * FROM order_items WHERE order_id = ?;

SELECT * FROM payments WHERE order_id = ?;
```
