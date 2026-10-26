def charge(amount, token):
    """Create a fictional payment receipt; no payment provider is contacted."""
    if amount < 0 or not token:
        raise ValueError("Invalid payment")
    return {"amount": amount, "status": "paid"}


def refund(receipt):
    """Return a refund record for an existing payment receipt."""
    return {"amount": receipt["amount"], "status": "refunded"}
