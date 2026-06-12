from typing import overload

from Core.Function.BinaryOperations.BinaryOperation import BinaryOperation
from Core.Function.FunctionInterpreter.LexicalBlocks.OperationPrecidence import OperationPrecedence
from Core.Set.FiniteSet import FiniteSet
from Core.Set.Interval import Interval
from Core.Set.IntervalSet import IntervalSet
from Core.Set.Set import Set


class Addition(BinaryOperation):

    def __init__(self):
        super().__init__("+", 0, precedence=OperationPrecedence.ADDITION)

    @overload
    def calculate(self, A: Set, b: float, maintain: bool = True) -> Set:
        if isinstance(A, IntervalSet):
            out = A.copy() if maintain and hasattr(A, "copy") else A
            intervals = []
            for interval in out.intervals:
                if interval.is_empty():
                    continue
                intervals.append(
                    Interval(
                        interval.a + b,
                        interval.b + b,
                        interval.left_open,
                        interval.right_open,
                    )
                )
            return IntervalSet(*intervals)

        if hasattr(A, "elements"):
            return FiniteSet(*[a + b for a in A.elements])

        raise TypeError(f"Unsupported Set type for addition: {type(A).__name__}")

    @overload
    def calculate(self, a: float, b: float) -> float:
        return a + b

    def calculate(self, a, b, maintain: bool = True):
        if isinstance(a, Set):
            return self.transform_set_right(a, b, maintain)

        return a + b

    def transform_set_right(self, A: Set, b: float, maintain: bool = True) -> Set:
        if isinstance(A, IntervalSet):
            out = A.copy() if maintain and hasattr(A, "copy") else A
            intervals = []
            for interval in out.intervals:
                if interval.is_empty():
                    continue
                intervals.append(
                    Interval(
                        interval.a + b,
                        interval.b + b,
                        interval.left_open,
                        interval.right_open,
                    )
                )
            return IntervalSet(*intervals)

        if hasattr(A, "elements"):
            return FiniteSet(*[a + b for a in A.elements])

        raise TypeError(f"Unsupported Set type for addition: {type(A).__name__}")

    @overload
    def invert(self, a: float) -> float | None:
        """Return the additive inverse of a (i.e. -a). Always defined for numbers."""
        try:
            return -a
        except Exception:
            return None

    @overload
    def invert(self, A: Set) -> Set | None:
        """Return the additive inverse of a set (i.e. -A). Always defined for sets of numbers."""
        if isinstance(A, IntervalSet):
            intervals = []
            for interval in A.intervals:
                if interval.is_empty():
                    continue
                intervals.append(
                    Interval(
                        -interval.b,
                        -interval.a,
                        interval.right_open,
                        interval.left_open,
                    )
                )
            return IntervalSet(*intervals)

        if hasattr(A, "elements"):
            return FiniteSet(*[-a for a in A.elements])

        raise TypeError(f"Unsupported Set type for inversion: {type(A).__name__}")

    def invert(self, *n: float) -> Set | None:
        return self.invert(FiniteSet(*n))

