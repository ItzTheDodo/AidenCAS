from Core.Function.BinaryOperations.Negation import Negation
from Core.Function.FunctionInterpreter.LexicalBlocks.LexicalBlock import LexicalBlock, LexicalBlockType


class LexUnaryOperation(LexicalBlock):

    def __init__(self, char: str, precedence: int, unary_operation: Negation):
        super().__init__(char, LexicalBlockType.FUNCTIONAL, precedence, unary_operation)

    def __str__(self) -> str:
        return f"LexUnaryOperation({self.char}, {self.type}, {self.precedence}, {self.operation})"

    def __repr__(self) -> str:
        return self.__str__()
