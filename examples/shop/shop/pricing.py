"""Pricing policy: amounts are integer cents."""

def subtotal(items):
    """Calculate basket subtotal from item price and quantity."""
    return sum(item["price"] * item["quantity"] for item in items)


def discount(total, loyalty=False):
    """Apply a ten percent loyalty discount to the order price."""
    return total // 10 if loyalty else 0


def shipping(total):
    """Calculate delivery fee; orders of 300000 cents ship free."""
    return 0 if total >= 300000 else 25000


def quote(items, loyalty=False):
    """Compute the final order total including discount and shipping."""
    base = subtotal(items)
    discounted = base - discount(base, loyalty)
    return discounted + shipping(discounted)
