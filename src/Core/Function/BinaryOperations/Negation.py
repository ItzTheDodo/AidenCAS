from typing import overload

from Core.Function.BinaryOperations.BinaryOperation import BinaryOperation
from Core.Function.FunctionInterpreter.LexicalBlocks.OperationPrecidence import OperationPrecedence
from Core.Set.FiniteSet import FiniteSet
from Core.Set.Interval import Interval
from Core.Set.IntervalSet import IntervalSet
from Core.Set.Set import Set


class Negation(BinaryOperation):

    def __init__(self):
        super().__init__("neg", -1, associative=False, commutative=False, zero=0, precedence=OperationPrecedence.POWER)

    @overload
    def calculate(self, a: float) -> float:
        return -a

    @overload
    def calculate(self, A: Set) -> Set:
        if isinstance(A, IntervalSet):
            out = A.copy() if hasattr(A, "copy") else A
            intervals = []
            for interval in out.intervals:
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
            return FiniteSet(*[-x for x in A.elements])

        raise TypeError(f"Unsupported Set type for negation: {type(A).__name__}")

    def calculate(self, a, maintain: bool = True):
        if isinstance(a, Set):
            return self.transform_set(a, maintain)
        return -a

    def transform_set(self, A: Set, maintain: bool = True) -> Set:
        if isinstance(A, IntervalSet):
            out = A.copy() if maintain and hasattr(A, "copy") else A
            intervals = []
            for interval in out.intervals:
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
            return FiniteSet(*[-x for x in A.elements])

        raise TypeError(f"Unsupported Set type for negation: {type(A).__name__}")

    def __str__(self) -> str:
        return "Negation()"

    def __repr__(self) -> str:
        return self.__str__()
