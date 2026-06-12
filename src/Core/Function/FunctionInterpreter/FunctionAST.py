from __future__ import annotations

from Core.Function.FunctionInterpreter.LexicalBlocks.LexBinaryOperation import LexBinaryOperation
from Core.Function.FunctionInterpreter.LexicalBlocks.LexFunction import LexFunction
from Core.Function.FunctionInterpreter.LexicalBlocks.LexLiterals import Identifier, Literal, CloseBracket, OpenBracket
from Core.Function.FunctionInterpreter.LexicalBlocks.LexicalBlock import LexicalBlock
from Core.Namespace.Namespace import Namespace

class FunctionASTNode:

    def __init__(self, acc: LexicalBlock):

        self._acc = acc
        self._children: list[FunctionASTNode] = []

    @property
    def actual(self) -> LexicalBlock:
        return self._acc

    @property
    def children(self) -> list[FunctionASTNode]:
        return self._children


class FunctionAST:

    def __init__(self):

        self._root: FunctionASTNode | None = None

    @property
    def root(self) -> FunctionASTNode | None:
        return self._root

    def set_root(self, node: FunctionASTNode):
        self._root = node

    @staticmethod
    def tokenise(expression: str, namespace: Namespace, argument_variables: list[str]) -> list[LexicalBlock]:

        tokens: list[LexicalBlock] = []
        current_num_buffer: str = ""
        current_func_buffer: str = ""

        for i, character in enumerate(expression):

            # check if currently reading a number
            if current_num_buffer:

                # take priority in reading number
                if character.isdigit():
                    current_num_buffer += character
                    continue

                # if at end of number then submit number and continue lexical analysis
                tokens.append(Literal(current_num_buffer))
                current_num_buffer = ""

            # check if currently reading a function name
            if current_func_buffer:

                # break on close bracket
                if character == ")":
                    if not namespace.is_in_function_namespace(current_func_buffer):
                        raise ValueError(f"Invalid function name: {current_func_buffer}")

                    function = namespace.functions[current_func_buffer]
                    tokens.append(LexFunction(current_func_buffer, function))
                    tokens.append(CloseBracket(character))
                    current_func_buffer = ""
                    continue

                # check if we are reading last character of expression
                if i + 1 == len(expression):
                    raise ValueError(f"Malformed function expression, unknown reference '{current_func_buffer[0]}' from '{current_func_buffer}' in {expression}")

                # carry on reading string
                current_func_buffer += character
                continue

            print(character)


            # check for specific value
            if character == ")":
                tokens.append(CloseBracket(character))
                continue
            if character == "(":
                tokens.append(OpenBracket(character))
                continue
            # checking for identifiers
            if character in argument_variables:
                tokens.append(Identifier(character))
                continue
            # checking for literals
            if character.isdigit():
                current_num_buffer += character
                continue
            # checking for known binary operation
            if namespace.is_in_binary_operation_namespace(character):
                binary_operation = namespace.binary_operations[character]
                tokens.append(LexBinaryOperation(character, binary_operation.precedence, binary_operation))
                continue

            # checking for known function
            current_func_buffer += character

        return tokens

    @classmethod
    def from_mapping(cls, expression: str, namespace: Namespace, argument_variables: list[str]) -> FunctionAST:

        print(expression)
        print(namespace)
        print(argument_variables)

        lex_tokens = cls.tokenise(expression, namespace, argument_variables)

        print(lex_tokens)
