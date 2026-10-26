# Library service

## Borrowing a book

`borrow` authenticates the reader, searches the catalog using `find_book`, and calls
`reserve_book`. A reservation requires an available copy.

## Returning books

`return_book` closes a loan through `close_loan`. The `late_fee` function calculates
an overdue charge of ten units for each late day. Early returns have no fee.

## Reader access

`authenticate` looks up the reader account by access token. Unknown tokens do not
identify a reader. This fixture uses an in-memory dictionary, not production auth.
