def confirmation(order):
    """Format an order confirmation notification for the customer."""
    return f'Order confirmed: {order["receipt"]["amount"]} cents'
