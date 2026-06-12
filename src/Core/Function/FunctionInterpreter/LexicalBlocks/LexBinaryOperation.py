from Core.Function.BinaryOperations.BinaryOperation import BinaryOperation
from Core.Function.FunctionInterpreter.LexicalBlocks.LexicalBlock import LexicalBlock, LexicalBlockType


class LexBinaryOperation(LexicalBlock):

    def __init__(self, char: str, precedence: int, binop: BinaryOperation):
        super().__init__(char, LexicalBlockType.FUNCTIONAL, precedence, binop)
