from .pricing import quote
from .inventory import reserve
from .payments import charge
from .notifications import confirmation


def checkout(items, stock, token, loyalty=False):
    """Place an order: reserve stock, calculate total, charge and notify."""
    reserve(stock, items)
    amount = quote(items, loyalty)
    receipt = charge(amount, token)
    order = {"items": items, "receipt": receipt}
    order["message"] = confirmation(order)
    return order
