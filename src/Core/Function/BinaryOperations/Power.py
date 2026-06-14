from typing import overload

from Core.Function.BinaryOperations.BinaryOperation import BinaryOperation
from Core.Function.FunctionInterpreter.LexicalBlocks.OperationPrecidence import OperationPrecedence
from Core.Set.FiniteSet import FiniteSet
from Core.Set.Set import Set


class Power(BinaryOperation):

    def __init__(self):
        super().__init__("^", 1, associative=False, commutative=False, zero=0, precedence=OperationPrecedence.POWER, right_associative=True)

    @overload
    def calculate(self, a: float, b: float) -> float:
        return a ** b

    @overload
    def calculate(self, A: Set, b: float, maintain: bool = True) -> Set:
        if hasattr(A, "elements"):
            return FiniteSet(*[x ** b for x in A.elements])
        raise TypeError(f"Unsupported Set type for power: {type(A).__name__}")

    def calculate(self, a, b, maintain: bool = True):
        if isinstance(a, Set):
            return self.transform_set_right(a, b, maintain)
        return a ** b

    def transform_set_right(self, A: Set, b: float, maintain: bool = True) -> Set:
        if hasattr(A, "elements"):
            return FiniteSet(*[x ** b for x in A.elements])
        raise TypeError(f"Unsupported Set type for power: {type(A).__name__}")

    def __str__(self) -> str:
        return "Power()"

    def __repr__(self) -> str:
        return self.__str__()
