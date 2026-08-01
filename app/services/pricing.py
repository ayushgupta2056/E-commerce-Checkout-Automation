from decimal import Decimal, ROUND_HALF_UP

TAX_RATE = Decimal("0.08")
DISCOUNT_RATE = Decimal("0.10")
VALID_DISCOUNT_CODE = "SAVE10"


def money(value: float | Decimal) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_totals(subtotal: float, discount_code: str | None = None) -> dict[str, float]:
    subtotal_money = money(subtotal)
    tax = money(Decimal(str(subtotal_money)) * TAX_RATE)
    discount = money(Decimal(str(subtotal_money)) * DISCOUNT_RATE) if discount_code == VALID_DISCOUNT_CODE else 0.00
    final_total = money(Decimal(str(subtotal_money)) + Decimal(str(tax)) - Decimal(str(discount)))
    return {
        "subtotal": subtotal_money,
        "tax": tax,
        "discount": discount,
        "final_total": final_total,
    }
