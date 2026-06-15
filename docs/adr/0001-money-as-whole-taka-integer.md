# Money is stored as a whole-Taka integer

Prices and all monetary amounts are stored as **integers in whole Taka** (৳1,450 →
`1450`), with currency `"BDT"`. We deliberately do **not** use floats (rounding
bugs) and do **not** use minor units / poisha (`145000`).

## Why

The usual "store money in minor units" rule exists to avoid float errors and to
preserve sub-units. Whole-Taka integers already avoid float, and the sub-unit
(poisha, 1/100 Taka) is defunct in Bangladeshi retail — no price, shipping fee, or
discount in this shop is ever quoted in poisha, so minor-unit storage would just
append two always-`00` digits to every value.

## Consequences

- The API returns `price` as an integer and `currency: "BDT"`; the **frontend** formats
  it (`৳1,450`). The backend stays presentation-free.
- SSLCOMMERZ receives the integer amount directly — no unit conversion at the boundary.
- A future **percentage discount** could produce a fractional Taka (10% off ৳1,455 =
  ৳145.5). We accept this and will **round discounts to whole Taka** rather than
  switch storage to minor units. Revisit this ADR only if genuine sub-Taka precision
  is ever required.
