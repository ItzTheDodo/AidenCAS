from typing import overload, Optional

from Core.Set.Set import Set


class BinaryOperation:

    def __init__(self, name: str, identity: float, associative: bool = True, commutative: bool = True, zero: float = 0, precedence: int = 5, right_associative: bool = False):

        self._name = name

        self._identity = identity
        self._associative = associative
        self._commutative = commutative
        self._zero = zero
        self._precedence = precedence
        self._right_associative = right_associative

    @property
    def name(self) -> str:
        return self._name

    @property
    def identity(self) -> float:
        return self._identity

    @property
    def associative(self) -> bool:
        return self._associative

    @property
    def commutative(self) -> bool:
        return self._commutative

    @property
    def zero(self) -> float:
        return self._zero

    @property
    def precedence(self) -> int:
        return self._precedence

    @property
    def right_associative(self) -> bool:
        return self._right_associative

    @overload
    def calculate(self, A: Set, b: float, maintain: bool = True) -> Set: ...

    @overload
    def calculate(self, a: float, b: float) -> float: ...

    def calculate(self, *args, **kwargs) -> Set: ...

    def transform_set_right(self, A: Set, b: float, maintain: bool = True) -> Set:
        return self.calculate(A, b, maintain)

    @overload
    def invert(self, a: float) -> Optional[float]: ...

    @overload
    def invert(self, A: Set) -> Optional[Set]: ...

    def invert(self, *n: float) -> Optional[Set]: ...
