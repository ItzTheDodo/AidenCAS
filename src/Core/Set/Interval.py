from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Core.Set.IntervalSet import IntervalSet


class Interval:

    def __init__(self, a: float, b: float, left_open: bool = False, right_open: bool = False):

        self._a = b if a > b else a
        self._b = a if a > b else b
        self._left_open = True if self._a == float("-inf") else left_open
        self._right_open = True if self._b == float("inf") else right_open

    @property
    def a(self) -> float:
        return self._a

    @property
    def b(self) -> float:
        return self._b

    @property
    def left_open(self) -> bool:
        return self._left_open

    @property
    def right_open(self) -> bool:
        return self._right_open

    def __str__(self) -> str:
        return f"{"(" if self._left_open else "["}{self._a}, {self._b}{")" if self._right_open else "]"}"

    def __repr__(self) -> str:
        return f"Interval({self.a}, {self.b}, {self.left_open}, {self.right_open})"

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Interval):
            return False

        return self.a == o.a and self.b == o.b and self.left_open == o.left_open and self.right_open == o.right_open

    def __ne__(self, o: object) -> bool:
        return not self == o

    def copy(self) -> Interval:
        return Interval(self.a, self.b, self.left_open, self.right_open)

    def union(self, other: Interval) -> None | Interval:
        if self.b < other.a or other.b < self.a:
            return None

        # Only fail to merge if touching at a point where BOTH are open
        if self.b == other.a and self.right_open and other.left_open:
            return None

        if other.b == self.a and other.right_open and self.left_open:
            return None

        left_a = min(self.a, other.a)
        right_b = max(self.b, other.b)

        if self.a < other.a:
            left_open = self.left_open
        elif self.a > other.a:
            left_open = other.left_open
        else:
            left_open = self.left_open and other.left_open

        if self.b > other.b:
            right_open = self.right_open
        elif self.b < other.b:
            right_open = other.right_open
        else:
            right_open = self.right_open and other.right_open

        return Interval(left_a, right_b, left_open, right_open)

    def intersect(self, other: Interval) -> None | Interval:
        if self.b < other.a or other.b < self.a:
            return None

        if self.b == other.a and (self.right_open or other.left_open):
            return None

        if other.b == self.a and (other.right_open or self.left_open):
            return None

        left_a = max(self.a, other.a)
        right_b = min(self.b, other.b)

        if self.a > other.a:
            left_open = self.left_open
        elif self.a < other.a:
            left_open = other.left_open
        else:
            left_open = self.left_open or other.left_open

        if self.b < other.b:
            right_open = self.right_open
        elif self.b > other.b:
            right_open = other.right_open
        else:
            right_open = self.right_open or other.right_open

        if left_a == right_b and (left_open or right_open):
            return None

        return Interval(left_a, right_b, left_open, right_open)

    def is_empty(self) -> bool:
        return self.a == self.b and (self.left_open or self.right_open)

    def complement(self) -> IntervalSet:
        from Core.Set.IntervalSet import IntervalSet

        left_part = Interval(float('-inf'), self.a, False, not self.left_open)
        right_part = Interval(self.b, float('inf'), not self.right_open, False)

        return IntervalSet(left_part, right_part)

    def without(self, other: Interval) -> IntervalSet:
        from Core.Set.IntervalSet import IntervalSet

        return IntervalSet(self).intersect(other.complement())

    def contains(self, element: float) -> bool:
        if self.a < element < self.b:
            return True
        if element == self.a and not self.left_open:
            return True
        if element == self.b and not self.right_open:
            return True
        return False

    def __contains__(self, element: float) -> bool:
        return self.contains(element)

    def contains_interval(self, other: Interval) -> bool:
        if self.a > other.a or self.b < other.b:
            return False
        if self.a == other.a and self.left_open and not other.left_open:
            return False
        if self.b == other.b and self.right_open and not other.right_open:
            return False
        return True

    def to_set(self) -> IntervalSet:
        from Core.Set.IntervalSet import IntervalSet

        return IntervalSet(self)

    @a.setter
    def a(self, value):
        self._a = value

    @b.setter
    def b(self, value):
        self._b = value

    def is_singleton(self) -> bool:
        return self.a == self.b and not self.left_open and not self.right_open

    def get_singleton_element(self) -> float:
        if not self.is_singleton():
            raise ValueError("Interval is not a singleton.")
        return self.a


if __name__ == "__main__":

    a = Interval(1, 2)
    b = Interval(0, 1)
    c = Interval(-2, -1, True)
    d = Interval(2, 3, True, True)
    e = Interval(1.5, 3, True, True)
    f = Interval(1, 2, True, True)
    g = Interval(2, 2, True, True)

    print(a, b, c, d, e, f)

    assert a.union(b) == Interval(0, 2)
    assert a.union(c) is None
    assert d.union(a) == Interval(1, 3, False, True)
    assert a.union(d) == d.union(a)
    assert e.union(a) == Interval(1, 3, False, True)
    assert a.union(e) == e.union(a)
    assert a.union(f) == Interval(1, 2)
    assert a.union(f) == f.union(a)
    assert a.union(g) == Interval(1, 2)
    assert a.union(g) == g.union(a)

    assert a.intersect(b) == Interval(1, 1)
    assert a.intersect(c) is None
    assert d.intersect(a) is None
    assert d.intersect(a) == a.intersect(d)
    assert e.intersect(a) == Interval(1.5, 2, True)
    assert e.intersect(a) == a.intersect(e)
    assert a.intersect(f) == Interval(1, 2, True, True)
    assert a.intersect(f) == f.intersect(a)
    assert a.intersect(g) is None
    assert a.intersect(g) == g.intersect(a)
