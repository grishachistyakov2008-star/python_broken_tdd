"""Order checkout.

The rules live in `src/shop/specs/checkout.md` - read it first.
Both functions below are stubs: their signature is final, the bodies are yours.
Do not change the constants: the tests rely on them.
"""

from shop.money import percent_of

PROMO_CODES = {"WELCOME10": 10, "SUMMER15": 15, "VIP35": 35}
SUPPORTED_CITIES = ("msk", "spb")
MAX_DISCOUNT_PERCENT = 30
VAT_PERCENT = 20
SHIPPING_KOPEKS = 49_000
FREE_DELIVERY_FROM_KOPEKS = 500_000
TIER_DISCOUNTS = ((10, 5), (25, 10), (50, 15))
REQUIRED_LINE_KEYS = ("sku", "qty", "unit_price_kopecks")


def validate_order(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> str | None:
    """Return a human readable reason why the order is invalid, or None if it is fine."""
    if not lines:
        return "An order must contain at least one line."

    seen_skus: set[str] = set()
    for position, order_line in enumerate(lines, start=1):
        line_error = _validate_line(order_line, position, seen_skus)
        if line_error is not None:
            return line_error

    if promo_code and promo_code not in PROMO_CODES:
        return "The promo code is not supported."
    if shipping_city and shipping_city not in SUPPORTED_CITIES:
        return "The shipping city is not supported."
    return None


def _validate_line(order_line: dict[str, str], position: int, seen_skus: set[str]) -> str | None:
    """Return a validation error for one line, if it has one."""
    if any(key not in order_line for key in REQUIRED_LINE_KEYS):
        return f"Line {position} is missing a required field."
    sku = order_line["sku"]
    if not sku:
        return f"Line {position} has an empty SKU."
    if sku in seen_skus:
        return f"SKU {sku} appears more than once."
    seen_skus.add(sku)

    quantity = order_line["qty"]
    if not _is_integer_text(quantity):
        return f"Line {position} has an invalid quantity."
    if int(quantity) <= 0:
        return f"Line {position} quantity must be positive."

    unit_price = order_line["unit_price_kopecks"]
    if not _is_integer_text(unit_price):
        return f"Line {position} has an invalid price."
    if int(unit_price) < 0:
        return f"Line {position} price cannot be negative."
    return None


def _is_integer_text(value: str) -> bool:
    """Return whether text follows the integer syntax accepted by int()."""
    text = value.strip()
    if text.startswith(("+", "-")):
        text = text[1:]
    groups = text.split("_")
    return bool(groups) and all(group and group.isdecimal() for group in groups)


def calculate_order_total(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> int | None:
    """Return the order total in kopecks, or None if the order is invalid."""
    if validate_order(lines, promo_code, shipping_city) is not None:
        return None

    subtotal = 0
    total_quantity = 0
    for order_line in lines:
        quantity = int(order_line["qty"])
        subtotal += quantity * int(order_line["unit_price_kopecks"])
        total_quantity += quantity

    tier_percent = 0
    for threshold, discount_percent in reversed(TIER_DISCOUNTS):
        if total_quantity >= threshold:
            tier_percent = discount_percent
            break

    promo_percent = PROMO_CODES.get(promo_code, 0)
    discount_percent = min(max(tier_percent, promo_percent), MAX_DISCOUNT_PERCENT)
    discounted_subtotal = subtotal - percent_of(subtotal, discount_percent)
    shipping = (
        SHIPPING_KOPEKS if shipping_city and discounted_subtotal < FREE_DELIVERY_FROM_KOPEKS else 0
    )
    base = discounted_subtotal + shipping
    return base + percent_of(base, VAT_PERCENT)
