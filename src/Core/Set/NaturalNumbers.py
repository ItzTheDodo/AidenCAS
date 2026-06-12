from __future__ import annotations

from Core.Set.FiniteSet import FiniteSet
from Core.Set.Interval import Interval
from Core.Set.IntervalSet import IntervalSet


class NaturalNumbers(IntervalSet):

    def __init__(self, *intervals):
        negative_numbers = IntervalSet(Interval(float("-inf"), 1, True, True))
        nn_intervals_set = IntervalSet(*intervals)
        new_intervals = nn_intervals_set.without(negative_numbers)
        super().__init__(*new_intervals.intervals)

        self._nn_clean()

    def _nn_clean(self):
        for i, interval in enumerate(super().intervals):
            if interval.left_open and not interval.a == float("inf"):
                super().intervals[i] = Interval(interval.a + 1, interval.b, False, interval.right_open)

            if interval.right_open and not interval.b == float("inf"):
                super().intervals[i] = Interval(interval.a, interval.b - 1, interval.left_open, False)

    def __str__(self) -> str:
        return super().__str__() + " ⊆ |N"

    def __repr__(self):
        return f"Natural Numbers({self.intervals})"

    def contains(self, element: float) -> bool:
        return super().contains(element) and element.is_integer()

    def union(self, other: IntervalSet) -> NaturalNumbers:
        return NaturalNumbers(*super().union(other).intervals)

    def intersect(self, other: IntervalSet) -> NaturalNumbers:
        return NaturalNumbers(*super().intersect(other).intervals)

    def complement(self) -> NaturalNumbers:
        return NaturalNumbers(*super().complement().intervals)

    def without(self, other: IntervalSet) -> NaturalNumbers:
        return NaturalNumbers(*super().without(other).intervals)

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
    nn = NaturalNumbers(Interval(float("-inf"), float("inf"), True, True))
    print(nn)

    a = Interval(1, 3).to_set()
    b = Interval(7, 12).to_set()

    print(nn.without(a))
    print(nn.without(b))
