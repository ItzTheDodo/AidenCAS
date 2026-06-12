from Core.Function.BinaryOperations.BinaryOperation import BinaryOperation
from Core.Function.FunctionInterpreter.LexicalBlocks.LexicalBlock import LexicalBlock, LexicalBlockType


class LexBinaryOperation(LexicalBlock):

    def __init__(self, char: str, precedence: int, binop: BinaryOperation):
        super().__init__(char, LexicalBlockType.FUNCTIONAL, precedence, binop)

    def __str__(self) -> str:
        return f"LexBinaryOperation({self.char}, {self.type}, {self.precedence}, {self.operation})"

    def __repr__(self) -> str:
        return self.__str__()
