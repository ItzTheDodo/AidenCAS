from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from Core.Function.BinaryOperations import BinaryOperation

if TYPE_CHECKING:
    from Core.Function.FunctionInterpreter.Function import Function


class LexicalBlockType:

    FUNCTIONAL = 0
    LITERAL = 1
    VARIABLE = 2


class LexicalBlock:

    def __init__(self, char: str, type_: int, precedence: int = -1, operation: Optional[Function | BinaryOperation] = None):

        self._char = char
        self._type = type_
        self._precedence = precedence
        self._operation = operation

    @property
    def char(self) -> str:
        return self._char

    @property
    def type(self) -> int:
        return self._type

    @property
    def operation(self) -> Optional[Function | BinaryOperation]:
        return self._operation

    def __str__(self) -> str:
        return f"LexicalBlock({self.char}, {self.type}, {self.operation})"

    def __repr__(self) -> str:
        return self.__str__()
