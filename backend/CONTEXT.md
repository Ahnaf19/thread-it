# Backend

The storefront domain model and API for Thread It — a single-shop apparel store.
Owns the catalog, cart, orders, and stock rules.

## Language

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
