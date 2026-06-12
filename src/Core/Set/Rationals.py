from __future__ import annotations

from fractions import Fraction

from Core.Set.Integers import Integers
from Core.Set.NaturalNumbers import NaturalNumbers
from Core.Set.Interval import Interval
from Core.Set.IntervalSet import IntervalSet


class Rationals(IntervalSet):

    def __init__(self, *intervals):
        super().__init__(*intervals)

    def __str__(self) -> str:
        return super().__str__() + " ⊆ \u211A"

    def __repr__(self):
        return f"Rationals({self.intervals})"

    def contains(self, element: float) -> bool:
        if not super().contains(float(element)):
            return False

        try:
            frac = Fraction(element).limit_denominator()
            return abs(float(frac) - element) < 1e-15
        except (ValueError, OverflowError):
            return False

    def contains_integer(self, element: float) -> bool:
        return super().contains(float(element)) and float(element).is_integer()

    def contains_in_range(self, min_val: float, max_val: float) -> bool:
        for interval in self.intervals:
            if interval.b >= min_val and interval.a <= max_val:
                return True
        return False

    def union(self, other: IntervalSet) -> Rationals:
        return Rationals(*super().union(other).intervals)

    def intersect(self, other: IntervalSet) -> NaturalNumbers | Integers | Rationals:
        if isinstance(other, NaturalNumbers):
            return other.intersect(self)
        if isinstance(other, Integers):
            return other.intersect(self)
        return Rationals(*super().intersect(other).intervals)

    def complement(self) -> Rationals:
        return Rationals(*super().complement().intervals)

    def without(self, other: IntervalSet) -> NaturalNumbers | Integers | Rationals:
        if isinstance(other, NaturalNumbers):
            return other.without(self)
        if isinstance(other, Integers):
            return other.without(self)
        return Rationals(*super().without(other).intervals)


if __name__ == "__main__":
    i = Rationals(Interval(float("-inf"), float("inf"), True, True))
    print(i)

    a = Interval(1, 3).to_set()
    b = Interval(7, 12).to_set()

    print(i.without(a))
    print(i.without(b))
