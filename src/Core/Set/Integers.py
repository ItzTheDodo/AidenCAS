from __future__ import annotations

from Core.Set.FiniteSet import FiniteSet
from Core.Set.NaturalNumbers import NaturalNumbers
from Core.Set.Interval import Interval
from Core.Set.IntervalSet import IntervalSet


class Integers(IntervalSet):

    def __init__(self, *intervals):
        super().__init__(*intervals)

        self._int_clean()

    def _int_clean(self):
        for i, interval in enumerate(super().intervals):
            if interval.left_open and not interval.a == float("-inf"):
                super().intervals[i] = Interval(interval.a + 1, interval.b, False, interval.right_open)

            if interval.right_open and not interval.b == float("inf"):
                super().intervals[i] = Interval(interval.a, interval.b - 1, interval.left_open, False)

    def __str__(self) -> str:
        return super().__str__() + " ⊆ \u2124"

    def __repr__(self):
        return f"Integers({self.intervals})"

    def contains(self, element: float) -> bool:
        return super().contains(element) and element.is_integer()

    def union(self, other: IntervalSet) -> Integers:
        return Integers(*super().union(other).intervals)

    def intersect(self, other: IntervalSet) -> NaturalNumbers | Integers:
        if isinstance(other, NaturalNumbers):
            return other.intersect(self)
        return Integers(*super().intersect(other).intervals)

    def complement(self) -> Integers:
        return Integers(*super().complement().intervals)

    def without(self, other: IntervalSet) -> NaturalNumbers | Integers:
        if isinstance(other, NaturalNumbers):
            return other.without(self)
        return Integers(*super().without(other).intervals)

    def is_finite(self) -> bool:
        # check if all intervals are finite and there are no infinite intervals
        for interval in self.intervals:
            if interval.a == float("-inf") or interval.b == float("inf"):
                return False
        return True

    def to_finite_set(self) -> FiniteSet:
        if not self.is_finite():
            raise ValueError("Cannot convert to FiniteSet: contains infinite intervals.")
        elements = set()
        for interval in self.intervals:
            elements.update(range(int(interval.a), int(interval.b) + 1))
        return FiniteSet(*elements)


if __name__ == "__main__":
    i = Integers(Interval(float("-inf"), float("inf"), True, True))
    print(i)

    a = Interval(1, 3).to_set()
    b = Interval(7, 12).to_set()

    print(i.without(a))
    print(i.without(b))
