"""Catalog service for a fictional public library."""

def find_book(catalog, title):
    """Search the catalog for a book by title."""
    return [book for book in catalog if title.lower() in book['title'].lower()]


def available_copies(book):
    """Count copies of a book that are currently available to borrow."""
    return max(0, book['copies'] - book['borrowed'])


def reserve_book(book, reader):
    """Reserve an available copy for a library reader."""
    if available_copies(book) == 0:
        raise ValueError('No copies available')
    return {'book': book['id'], 'reader': reader['id']}
