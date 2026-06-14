# Number system helpers

These classes provide lightweight algebraic wrappers around sets and binary operations.

## Group

`Group(set, operation)` associates a set with a binary operation.

## Ring

`Ring(set, add_operation, mul_operation)` wraps:

- an underlying set
- an additive group
- a multiplicative operation

It also exposes:

- `zero_divisors`
- `units`
- `is_integral_domain()`
- `is_division_ring()`
- `is_field()`

## Notes

This layer is intentionally small. It uses the set/binary-operation model from the rest of the core rather than introducing a separate algebra engine.

