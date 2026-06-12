from typing import overload

from Core.Function.BinaryOperations.BinaryOperation import BinaryOperation
from Core.Function.FunctionInterpreter.LexicalBlocks.OperationPrecidence import OperationPrecedence
from Core.Set.FiniteSet import FiniteSet
from Core.Set.Interval import Interval
from Core.Set.IntervalSet import IntervalSet
from Core.Set.Set import Set


class Subtraction(BinaryOperation):

    def __init__(self):
        super().__init__("-", 0, associative=False, commutative=False, zero=0, precedence=OperationPrecedence.ADDITION)

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
                        interval.a - b,
                        interval.b - b,
                        interval.left_open,
                        interval.right_open,
                    )
                )
            return IntervalSet(*intervals)

        if hasattr(A, "elements"):
            return FiniteSet(*[a - b for a in A.elements])

        raise TypeError(f"Unsupported Set type for subtraction: {type(A).__name__}")

    @overload
    def calculate(self, a: float, b: float) -> float:
        return a - b

    def calculate(self, a, b, maintain: bool = True):
        if isinstance(a, Set):
            return self.transform_set_right(a, b, maintain)

        return a - b

    def transform_set_right(self, A: Set, b: float, maintain: bool = True) -> Set:
        if isinstance(A, IntervalSet):
            out = A.copy() if maintain and hasattr(A, "copy") else A
            intervals = []
            for interval in out.intervals:
                if interval.is_empty():
                    continue
                intervals.append(
                    Interval(
                        interval.a - b,
                        interval.b - b,
                        interval.left_open,
                        interval.right_open,
                    )
                )
            return IntervalSet(*intervals)

        if hasattr(A, "elements"):
            return FiniteSet(*[a - b for a in A.elements])

        raise TypeError(f"Unsupported Set type for subtraction: {type(A).__name__}")

    def __str__(self) -> str:
        return "Subtraction()"

    def __repr__(self) -> str:
        return self.__str__()
