from .catalog import find_book, reserve_book
from .accounts import authenticate, close_loan


def borrow(catalog, title, token, readers):
    """Authenticate a reader, search for a book and create a reservation."""
    reader = authenticate(token, readers)
    if reader is None:
        raise ValueError('Unknown reader')
    books = find_book(catalog, title)
    if not books:
        raise ValueError('Book not found')
    return reserve_book(books[0], reader)


def return_book(loan, days):
    """Accept a returned book and close the loan."""
    return close_loan(loan, days)
