def available(stock, sku, quantity):
    """Check whether warehouse stock contains the requested quantity."""
    return stock.get(sku, 0) >= quantity


def reserve(stock, items):
    """Validate inventory and reserve products before checkout."""
    for item in items:
        if not available(stock, item["sku"], item["quantity"]):
            raise ValueError("Insufficient stock")
    for item in items:
        stock[item["sku"]] -= item["quantity"]
    return stock
