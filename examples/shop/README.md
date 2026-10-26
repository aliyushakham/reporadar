# MiniShop exploration fixture

A fictional synchronous store. Amounts are integer cents. This deliberately small
example is a navigation fixture, not a production commerce application: reservation
has no transaction rollback and payment functions only construct dictionaries.

## Order lifecycle

`submit_order` calls `checkout`. Checkout reserves inventory, obtains a price quote,
creates a payment receipt and formats a customer confirmation.

## Price calculation

`quote` computes `subtotal`, applies `discount` and adds `shipping`.
Loyalty customers receive a 10% discount. Free shipping starts at 300000 cents
**after** the discount. Changes to `discount` can affect `quote`, `checkout`, and
`submit_order` through the static call graph.

## Inventory reservation

`reserve` checks `available` for each item before decrementing warehouse stock.
Insufficient stock raises ValueError. Duplicate SKU aggregation is outside this fixture.

## Payments and refunds

`charge` returns a fictional receipt. `cancel_order` calls `refund`.
No real payment API is used, and no credentials are needed.

## Customer notifications

`confirmation` formats a notification. The example never sends email or messages.
