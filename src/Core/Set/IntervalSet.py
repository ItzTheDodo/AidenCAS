from __future__ import annotations

from Core.Set.Interval import Interval
from Core.Set.Set import Set


class IntervalSet(Set):

    def __init__(self, *intervals: Interval):

        super().__init__()
        self._intervals = list(intervals)
        self._clean()

    @property
    def intervals(self) -> list[Interval]:
        return self._intervals

    def __str__(self) -> str:
        return " ∪ ".join(map(str, self.intervals))

    def __repr__(self):
        return f"Set({self.intervals})"

    def __eq__(self, other: IntervalSet) -> bool:
        if not isinstance(other, IntervalSet):
            return False

        in_set = []
        for interval in self.intervals:
            in_set.append(any([interval == ointerval for ointerval in other.intervals]))
        return all(in_set)

    def __ne__(self, other: IntervalSet) -> bool:
        return not self == other

    def __contains__(self, element: float) -> bool:
        for interval in self.intervals:
            if interval.contains(element):
                return True
        return False

    def _clean(self):
        if not self._intervals:
            return

        # Filter out empty intervals
        non_empty = [i for i in self._intervals if not i.is_empty()]

        if not non_empty:
            self._intervals = []
            return

        sorted_intervals = sorted(non_empty, key=lambda i: (i.a, i.b))

        merged = [sorted_intervals[0]]

        for current in sorted_intervals[1:]:
            last = merged[-1]
            union = last.union(current)

            if union is not None:
                merged[-1] = union
            else:
                merged.append(current)

        self._intervals = merged

    def to_interval(self) -> Interval:
        if len(self.intervals) > 1:
            raise Exception(f"Unable to convert to interval - Too many sets for minimum composition: {self}")

        if len(self.intervals) == 0:
            return Interval(0, 0, True, True)

        return self.intervals[0]

    def union(self, other: IntervalSet) -> IntervalSet:
        return IntervalSet(*self.intervals, *other.intervals)

    def intersect(self, other: IntervalSet) -> IntervalSet:
        intersections = []

        for interval1 in self.intervals:
            for interval2 in other.intervals:
                intersection = interval1.intersect(interval2)
                if intersection is not None:
                    intersections.append(intersection)

        return IntervalSet(*intersections) if intersections else IntervalSet()

    def complement(self) -> IntervalSet:
        if not self.intervals:
            return IntervalSet(Interval(float('-inf'), float('inf'), True, True))

        complement_intervals = []

        first = self.intervals[0]
        if first.a > float('-inf'):
            left_complement = Interval(
                float('-inf'),
                first.a,
                True,
                not first.left_open
            )
            if not left_complement.is_empty():
                complement_intervals.append(left_complement)

        for i in range(len(self.intervals) - 1):
            current = self.intervals[i]
            next_interval = self.intervals[i + 1]

            gap = Interval(
                current.b,
                next_interval.a,
                not current.right_open,
                not next_interval.left_open
            )
            if not gap.is_empty():
                complement_intervals.append(gap)

        last = self.intervals[-1]
        if last.b < float('inf'):
            right_complement = Interval(
                last.b,
                float('inf'),
                not last.right_open,
                True
            )
            if not right_complement.is_empty():
                complement_intervals.append(right_complement)

        return IntervalSet(*complement_intervals) if complement_intervals else IntervalSet()

    def without(self, other: IntervalSet) -> IntervalSet:
        return self.intersect(other.complement())

    def contains(self, element: float) -> bool:
        for interval in self.intervals:
            if interval.contains(element):
                return True
        return False

    def copy(self) -> IntervalSet:
        return IntervalSet(*[i.copy() for i in self.intervals])

    def is_empty(self) -> bool:
        return len(self.intervals) == 0

    def is_singleton(self) -> bool:
        return len(self.intervals) == 1 and self.intervals[0].is_singleton()

    def get_singleton_element(self) -> float:
        if not self.is_singleton():
            raise ValueError("IntervalSet is not a singleton.")
        return self.intervals[0].get_singleton_element()


if __name__ == "__main__":

    a = Interval(1, 2)
    b = Interval(0, 1)
    c = Interval(-2, -1, True)
    d = Interval(2, 3, True, True)
    e = Interval(1.5, 3, True, True)
    f = Interval(1, 2, True, True)
    g = Interval(2, 2, True, True)
    h = Interval(3, 3, True, True)

    s = IntervalSet(a, f, c, g)
    t = IntervalSet(a, e, d, f, g, h)
    u = IntervalSet(a, g, h)
    v = IntervalSet(a, f)
    w = IntervalSet(g, h)
    print(s)
    print(t)
    print(u)
    print(v)
    print(w)

    assert Interval(1, 2) in s.intervals
    assert Interval(-2, -1, True) in s.intervals
    assert t.to_interval() == Interval(1, 3, False, True)
    assert u.to_interval() == a
    assert v.to_interval() == a

    assert c in s.union(t).intervals
    assert Interval(1, 3, False, True) in s.union(t).intervals
    assert s.union(t) == t.union(s)
    assert a == u.union(v).to_interval()
    assert u.union(v) == v.union(u)
    assert a == u.union(w).to_interval()
    assert u.union(w) == w.union(u)

    # Test intersection
    s_int = IntervalSet(Interval(1, 4), Interval(6, 8))
    t_int = IntervalSet(Interval(2, 7))
    result_int = s_int.intersect(t_int)
    assert Interval(2, 4) in result_int.intervals
    assert Interval(6, 7) in result_int.intervals
    assert s_int.intersect(t_int) == t_int.intersect(s_int)

    no_overlap = IntervalSet(Interval(1, 2)).intersect(IntervalSet(Interval(3, 4)))
    assert len(no_overlap.intervals) == 0

    s_comp1 = IntervalSet(Interval(1, 3))
    comp1 = s_comp1.complement()
    assert any(i.a == float('-inf') for i in comp1.intervals)
    assert any(i.b == float('inf') for i in comp1.intervals)

    s_comp2 = IntervalSet(Interval(1, 2), Interval(4, 5))
    comp2 = s_comp2.complement()
    assert len(comp2.intervals) == 3

    s_empty = IntervalSet()
    comp_empty = s_empty.complement()
    assert len(comp_empty.intervals) == 1
    assert comp_empty.intervals[0].a == float('-inf')
    assert comp_empty.intervals[0].b == float('inf')
