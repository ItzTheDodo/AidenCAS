from __future__ import annotations
from typing import TYPE_CHECKING

from Core.Function.FunctionInterpreter.LexicalBlocks.LexicalBlock import LexicalBlock, LexicalBlockType
from Core.Function.FunctionInterpreter.LexicalBlocks.OperationPrecidence import OperationPrecedence

if TYPE_CHECKING:
    from Core.Function.FunctionInterpreter.Function import Function


class LexFunction(LexicalBlock):

    def __init__(self, name: str, func: Function):
        super().__init__(name, LexicalBlockType.FUNCTIONAL, OperationPrecedence.BRACKETS, func)

    def __str__(self) -> str:
        return f"LexFunction({self.char}, {self.type}, {self.precedence}, {self.operation})"

    def __repr__(self) -> str:
        return self.__str__()
