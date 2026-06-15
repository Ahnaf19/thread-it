# Backend

The storefront domain model and API for Thread It — a single-shop apparel store.
Owns the catalog, cart, orders, and stock rules.

## Language

### Roles

**Admin**:
The single shop owner who manages the catalog (products, per-size stock). The only
authenticated actor in v1 — credentials live in env, not a user table (see ADR-0005).
_Avoid_: User, Staff, Seller (there is exactly one, and customers are unauthenticated guests in v1)

### Catalog

**Product**:
A catalog item a shopper browses (e.g. "Linen Oversized Shirt"). Holds presentation
and pricing; never holds stock directly.
_Avoid_: Item, SKU (a Product is not the stock-keeping unit — a Variant is)

**Variant**:
A single buyable option of a Product and the unit that carries stock. For now a
Variant is a (Product × Size) pair; "Linen Shirt / M" is one Variant. Accessories
and one-size goods have exactly one Variant.
_Avoid_: SKU, Option, ProductSize

**Category**:
The single apparel grouping a Product belongs to, from a fixed ordered set:
`Tops, Bottoms, Outerwear, Dresses, Accessories`. Drives the catalog `?category=`
filter. Each Product has exactly one.
_Avoid_: free-form categories, tags, collections, multiple categories per product (v1)

**Stock**:
The count of a single Variant available to sell. Lives on the Variant, never on the
Product. Decremented when an order is paid (naive in v1; concurrency-safe in v2).
_Avoid_: Inventory, Quantity (reserve "quantity" for cart line items)

**Size**:
A Variant's size, drawn from a fixed, ordered set: `XS, S, M, L, XL, XXL, One Size`.
The order is display order (the size selector shows S→M→L, never alphabetical).
_Avoid_: free-form size labels, numeric/waist sizing (not supported in v1)

**One Size**:
The canonical Size value for a Product that isn't sized (accessories). Keeps every
Product sellable through exactly one+ Variant with no special-casing.

### Cart

**Cart**:
A guest's prospective purchase — a list of Line Items. Held client-side (browser)
in v1, not persisted on the server. The backend prices and validates it on demand
but never stores it.
_Avoid_: Basket, Order (an Order is the committed, paid thing — a Cart is not)

**Line Item**:
One Variant plus a Quantity within a Cart.
_Avoid_: Cart entry, Order line (reserve "Order line" for the Order, post-checkout)

**Quantity**:
The count of a single Variant in a Line Item. Clamped to the Variant's current Stock
when the Cart is priced.

**Subtotal**:
The sum of Line Item totals (unit price × Quantity) in a Cart, before any shipping
or tax. v1 has no shipping or tax, so the Subtotal is the cart total.
_Avoid_: Total, Grand total (no shipping/tax layer exists yet)

### Orders

**Order**:
A guest's committed purchase. Created in `pending` status at checkout (before the
payment redirect) and confirmed `paid` when SSLCOMMERZ reports success. Carries the
guest's contact/shipping details and a total snapshot.
_Avoid_: Cart (a Cart is the pre-checkout, client-side thing; an Order is server-persisted)

**Order Item**:
A line of an Order. **Snapshots** product name, size, unit price, and quantity at
checkout time — so the Order is stable even if the catalog later changes. Distinct
from a Cart's Line Item, which references the live catalog.
_Avoid_: Line Item (reserve that for the Cart)

**Order status**:
The Order's lifecycle: `pending` → `paid` → (`failed` / `cancelled`). v1 transitions
are naive but guarded against double-application; concurrency-safe, exactly-once
handling is v2.
_Avoid_: state, phase
