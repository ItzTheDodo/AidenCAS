from typing import overload

from Core.Function.BinaryOperations.BinaryOperation import BinaryOperation
from Core.Function.FunctionInterpreter.LexicalBlocks.OperationPrecidence import OperationPrecedence
from Core.Set.FiniteSet import FiniteSet
from Core.Set.Interval import Interval
from Core.Set.IntervalSet import IntervalSet
from Core.Set.Set import Set


class Multiplication(BinaryOperation):

    def __init__(self):
        super().__init__("*", 1, precedence=OperationPrecedence.MULTIPLICATION)

    @overload
    def calculate(self, A: Set, b: float, maintain: bool = True) -> Set:
        if isinstance(A, IntervalSet):
            out = A.copy() if maintain and hasattr(A, "copy") else A
            new_intervals = []
            for interval in out.intervals:
                if interval.is_empty():
                    continue
                if b == 0:
                    new_intervals.append(Interval(0, 0, False, False))
                    continue

                a1 = interval.a * b
                b1 = interval.b * b
                lo = min(a1, b1)
                hi = max(a1, b1)

                if b > 0:
                    left_open = interval.left_open
                    right_open = interval.right_open
                else:
                    left_open = interval.right_open
                    right_open = interval.left_open

                new_intervals.append(Interval(lo, hi, left_open, right_open))

            return IntervalSet(*new_intervals)

        if hasattr(A, "elements"):
            return FiniteSet(*[x * b for x in A.elements])

        raise TypeError(f"Unsupported Set type for multiplication: {type(A).__name__}")

    @overload
    def calculate(self, a: float, b: float) -> float:
        return a * b

    def calculate(self, a, b, maintain: bool = True):
        if isinstance(a, Set):
            return self.transform_set_right(a, b, maintain)

        return a * b

    def transform_set_right(self, A: Set, b: float, maintain: bool = True) -> Set:
        if isinstance(A, IntervalSet):
            out = A.copy() if maintain and hasattr(A, "copy") else A
            new_intervals = []
            for interval in out.intervals:
                if interval.is_empty():
                    continue
                if b == 0:
                    new_intervals.append(Interval(0, 0, False, False))
                    continue

                a1 = interval.a * b
                b1 = interval.b * b
                lo = min(a1, b1)
                hi = max(a1, b1)

                if b > 0:
                    left_open = interval.left_open
                    right_open = interval.right_open
                else:
                    left_open = interval.right_open
                    right_open = interval.left_open

                new_intervals.append(Interval(lo, hi, left_open, right_open))

            return IntervalSet(*new_intervals)

        if hasattr(A, "elements"):
            return FiniteSet(*[x * b for x in A.elements])

        raise TypeError(f"Unsupported Set type for multiplication: {type(A).__name__}")

    @overload
    def invert(self, a: float) -> float | None:
        if a == 0:
            return None
        return 1 / a

    @overload
    def invert(self, A: Set) -> Set:
        if isinstance(A, IntervalSet):
            new_intervals = []
            for interval in A.intervals:
                if interval.is_empty():
                    continue
                if interval.a <= 0 <= interval.b:
                    if interval.a < 0:
                        new_intervals.append(Interval(float("-inf"), 1 / interval.a, True, True))
                    if interval.b > 0:
                        new_intervals.append(Interval(1 / interval.b, float("inf"), True, True))
                else:
                    a1 = 1 / interval.a
                    b1 = 1 / interval.b
                    lo = min(a1, b1)
                    hi = max(a1, b1)
                    left_open = interval.left_open
                    right_open = interval.right_open
                    new_intervals.append(Interval(lo, hi, left_open, right_open))

            return IntervalSet(*new_intervals)

        if hasattr(A, "elements"):
            inverted_elements = []
            for x in A.elements:
                inv = self.invert(x)
                if inv is not None:
                    inverted_elements.append(inv)
            return FiniteSet(*inverted_elements)

        raise TypeError(f"Unsupported Set type for inversion: {type(A).__name__}")

    def invert(self, *n: float) -> Set:
        return self.invert(FiniteSet(*n))


if __name__ == "__main__":
    from Core.Set.Integers import Integers
    from Core.Set.Rationals import Rationals

    m = Multiplication()

    # Test with random sets
    A = Integers(Interval(float("-inf"), float("inf"), True, True))
    B = Rationals(Interval(float("-inf"), float("inf"), True, True))
    C = FiniteSet(1, 2, 3, 4, 5)
    D = IntervalSet(Interval(1, 5, False, False), Interval(10, 15, True, True))

    print(m.calculate(A, 2))
    print(m.calculate(B, 0.5))
    print(m.calculate(C, 3))
    print(m.calculate(D, -1))

