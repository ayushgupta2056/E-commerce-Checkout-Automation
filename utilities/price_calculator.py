from decimal import Decimal, ROUND_HALF_UP

TAX_RATE = Decimal("0.08")
DISCOUNT_RATE = Decimal("0.10")


def money(value: float | Decimal) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_totals(subtotal: float, discount_code: str | None = None) -> dict[str, float]:
    rounded_subtotal = money(subtotal)
    tax = money(Decimal(str(rounded_subtotal)) * TAX_RATE)
    discount = money(Decimal(str(rounded_subtotal)) * DISCOUNT_RATE) if discount_code == "SAVE10" else 0.00
    final_total = money(Decimal(str(rounded_subtotal)) + Decimal(str(tax)) - Decimal(str(discount)))
    return {
        "subtotal": rounded_subtotal,
        "tax": tax,
        "discount": discount,
        "final_total": final_total,
    }
