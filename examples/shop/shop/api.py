from .checkout import checkout
from .payments import refund


def submit_order(payload, stock):
    """Handle the order endpoint and submit the customer basket."""
    return checkout(payload["items"], stock, payload["token"], payload.get("loyalty", False))


def cancel_order(receipt):
    """Cancel an order by issuing a payment refund."""
    return refund(receipt)
