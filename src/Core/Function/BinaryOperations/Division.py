from typing import overload

from Core.Function.BinaryOperations.BinaryOperation import BinaryOperation
from Core.Function.FunctionInterpreter.LexicalBlocks.OperationPrecidence import OperationPrecedence
from Core.Set.FiniteSet import FiniteSet
from Core.Set.Interval import Interval
from Core.Set.IntervalSet import IntervalSet
from Core.Set.Set import Set


class Division(BinaryOperation):

    def __init__(self):
        super().__init__("/", 1, associative=False, commutative=False, zero=0, precedence=OperationPrecedence.MULTIPLICATION)

    @overload
    def calculate(self, A: Set, b: float, maintain: bool = True) -> Set:
        if b == 0:
            raise ZeroDivisionError("Division by zero")

        return self.transform_set_right(A, b, maintain)

    @overload
    def calculate(self, a: float, b: float) -> float:
        return a / b

    def calculate(self, a, b, maintain: bool = True):
        if isinstance(a, Set):
            return self.transform_set_right(a, b, maintain)

        return a / b

    def transform_set_right(self, A: Set, b: float, maintain: bool = True) -> Set:
        if b == 0:
            raise ZeroDivisionError("Division by zero")

        factor = 1 / b

        if isinstance(A, IntervalSet):
            out = A.copy() if maintain and hasattr(A, "copy") else A
            new_intervals = []
            for interval in out.intervals:
                if interval.is_empty():
                    continue
                a1 = interval.a * factor
                b1 = interval.b * factor
                lo = min(a1, b1)
                hi = max(a1, b1)

                if factor > 0:
                    left_open = interval.left_open
                    right_open = interval.right_open
                else:
                    left_open = interval.right_open
                    right_open = interval.left_open

                new_intervals.append(Interval(lo, hi, left_open, right_open))

            return IntervalSet(*new_intervals)

        if hasattr(A, "elements"):
            return FiniteSet(*[x / b for x in A.elements])

        raise TypeError(f"Unsupported Set type for division: {type(A).__name__}")

    def __str__(self) -> str:
        return "Division()"

    def __repr__(self) -> str:
        return self.__str__()
