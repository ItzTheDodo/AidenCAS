from __future__ import annotations

from typing import overload

from Core.Set.Interval import Interval
from Core.Set.IntervalSet import IntervalSet
from Core.Set.Set import Set


class FiniteSet(Set):

    def __init__(self, *elements: float):

        self._elements = list(set(elements))

    @property
    def elements(self) -> list[float]:
        return self._elements

    def _truncate_max_elements(self) -> list[str]:
        MAX_ELEMENTS = 10
        elements_display = self.elements[:10] + ["..."] if len(self.elements) > MAX_ELEMENTS else self.elements
        return list(map(str, elements_display))

    def __str__(self) -> str:
        return "{" + ", ".join(self._truncate_max_elements()) + "}"

    def __repr__(self) -> str:
        return f"FiniteSet({", ".join(self._truncate_max_elements())})"

    def __eq__(self, other: FiniteSet) -> bool:
        if not isinstance(other, FiniteSet):
            return False

        for element in self.elements:
            if not element in other.elements:
                return False

        return True

    def __ne__(self, other: FiniteSet) -> bool:
        return not self == other

    def __contains__(self, item: float) -> bool:
        return item in self.elements

    def to_interval_set(self) -> IntervalSet:
        intervals = [Interval(i, i) for i in self.elements]
        return IntervalSet(*intervals)

    @overload
    def union(self, other: FiniteSet) -> FiniteSet:
        return FiniteSet(*set(*self.elements, *other.elements))

    @overload
    def union(self, other: IntervalSet) -> IntervalSet:
        return self.to_interval_set().union(other)

    def union(self, other: Set) -> Set:
        raise NotImplementedError

    @overload
    def intersect(self, other: FiniteSet) -> FiniteSet:
        return FiniteSet(*set(self.elements).intersection(set(other.elements)))

    @overload
    def intersect(self, other: IntervalSet) -> IntervalSet:
        return self.to_interval_set().intersect(other)

    def intersect(self, other: Set) -> Set:
       raise NotImplementedError()

    def complement(self) -> IntervalSet:
        return self.to_interval_set().complement()

    def contains(self, element: float) -> bool:
        return element in self.elements

    @overload
    def without(self, other: FiniteSet) -> FiniteSet:
        return FiniteSet(*[i for i in self.elements if i in other.elements])

    @overload
    def without(self, other: IntervalSet) -> IntervalSet:
        return self.to_interval_set().without(other)

    def without(self, other: Set) -> Set:
        raise NotImplementedError()

    def is_empty(self) -> bool:
        return len(self.elements) == 0

    def is_singleton(self) -> bool:
        return len(self.elements) == 1

    def copy(self) -> FiniteSet:
        return FiniteSet(*self.elements[:])

    def get_singleton_element(self) -> float:
        if not self.is_singleton():
            raise ValueError("Set is not a singleton.")
        return self.elements[0]
