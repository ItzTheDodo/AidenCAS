# Set subsystem

The set subsystem provides the domain objects used for function validation and algebraic wrappers.

## Types

- `Set` — common interface.
- `Interval` — single interval with open/closed endpoints.
- `IntervalSet` — union of intervals with merge/intersection/complement helpers.
- `FiniteSet` — finite collection of numeric elements.
- `Integers` — interval-based integer set.
- `NaturalNumbers` — interval-based natural-number set.
- `Rationals` — interval-based rational set with rational-membership checks.

## Interval conventions

- Intervals are normalized so `a <= b`.
- Open endpoints remain open at infinities.
- Interval unions merge overlapping/touching intervals when allowed by openness.
- Empty intervals are preserved only transiently and removed by cleanup.

## Common operations

- `union`
- `intersect`
- `complement`
- `without`
- `contains`
- `is_empty`
- `is_singleton`

## Notes

- `Integers`, `NaturalNumbers`, and `Rationals` inherit from `IntervalSet`.
- Membership checks are specialized where needed:
  - integers require integral values
  - naturals require positive integral values
  - rationals use a fraction-based approximation check

