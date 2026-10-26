def authenticate(token, readers):
    """Validate an access token and return the matching reader account."""
    return readers.get(token)


def late_fee(days):
    """Calculate overdue return fees from the number of late days."""
    return max(0, days) * 10


def close_loan(loan, days):
    """Close a returned book loan and calculate the late fee."""
    return {'loan': loan, 'fee': late_fee(days), 'closed': True}
