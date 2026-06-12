from Core.Function.FunctionInterpreter.LexicalBlocks.LexicalBlock import LexicalBlock, LexicalBlockType
from Core.Function.FunctionInterpreter.LexicalBlocks.OperationPrecidence import OperationPrecedence


class Identifier(LexicalBlock):

    def __init__(self, char: str):
        super().__init__(char, LexicalBlockType.VARIABLE)

    def __str__(self) -> str:
        return f"Identifier({self.char})"

    def __repr__(self) -> str:
        return self.__str__()


class Literal(LexicalBlock):

    def __init__(self, char: str):
        super().__init__(char, LexicalBlockType.LITERAL)

    def __str__(self) -> str:
        return f"Literal({self.char})"

    def __repr__(self) -> str:
        return self.__str__()


class CloseBracket(LexicalBlock):

    def __init__(self, char: str):
        super().__init__(char, LexicalBlockType.LITERAL, precedence=OperationPrecedence.BRACKETS)

    def __str__(self) -> str:
        return f"CloseBracket()"

    def __repr__(self) -> str:
        return self.__str__()


class OpenBracket(LexicalBlock):

    def __init__(self, char: str):
        super().__init__(char, LexicalBlockType.LITERAL, precedence=OperationPrecedence.BRACKETS)

    def __str__(self) -> str:
        return f"OpenBracket()"

    def __repr__(self) -> str:
        return self.__str__()


class Comma(LexicalBlock):

    def __init__(self, char: str):
        super().__init__(char, LexicalBlockType.LITERAL, precedence=OperationPrecedence.COMMA)

    def __str__(self) -> str:
        return f"Comma()"

    def __repr__(self) -> str:
        return self.__str__()

