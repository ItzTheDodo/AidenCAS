from __future__ import annotations

from dataclasses import dataclass

from Core.Function.FunctionInterpreter.LexicalBlocks.LexBinaryOperation import LexBinaryOperation
from Core.Function.FunctionInterpreter.LexicalBlocks.LexFunction import LexFunction
from Core.Function.FunctionInterpreter.LexicalBlocks.LexLiterals import Comma, CloseBracket, Identifier, Literal, OpenBracket
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

    def __str__(self) -> str:
        return f"FunctionASTNode({self.actual})"

    def __repr__(self) -> str:
        return self.__str__()


@dataclass
class _FunctionCallContext:
    arity: int = 1
    has_argument: bool = False


class FunctionAST:

    def __init__(self, root: FunctionASTNode):
        self._root = root

    @property
    def root(self) -> FunctionASTNode:
        return self._root

    def set_root(self, node: FunctionASTNode):
        self._root = node

    @staticmethod
    def tokenise(expression: str, namespace: Namespace, argument_variables: list[str]) -> list[LexicalBlock]:
        tokens: list[LexicalBlock] = []
        i = 0

        while i < len(expression):
            character = expression[i]

            if character.isspace():
                i += 1
                continue

            if character.isdigit():
                start = i
                while i < len(expression) and expression[i].isdigit():
                    i += 1
                tokens.append(Literal(expression[start:i]))
                continue

            if character.isalpha() or character in {"_", "|"}:
                start = i
                i += 1
                while i < len(expression) and (expression[i].isalnum() or expression[i] in {"_", "|"}):
                    i += 1

                name = expression[start:i]
                if name in argument_variables:
                    tokens.append(Identifier(name))
                    continue

                if namespace.is_in_function_namespace(name):
                    lookahead = i
                    while lookahead < len(expression) and expression[lookahead].isspace():
                        lookahead += 1
                    if lookahead >= len(expression) or expression[lookahead] != "(":
                        raise ValueError(f"Malformed function expression: expected '(' after function name '{name}'")
                    tokens.append(LexFunction(name, namespace.functions[name]))
                    continue

                raise ValueError(f"Unknown identifier or function name: {name}")

            if character == "(":
                tokens.append(OpenBracket(character))
                i += 1
                continue

            if character == ")":
                tokens.append(CloseBracket(character))
                i += 1
                continue

            if character == ",":
                tokens.append(Comma(character))
                i += 1
                continue

            if namespace.is_in_binary_operation_namespace(character):
                binary_operation = namespace.binary_operations[character]
                tokens.append(LexBinaryOperation(character, binary_operation.precedence, binary_operation))
                i += 1
                continue

            raise ValueError(f"Unexpected character '{character}' in expression: {expression}")

        return tokens

    @staticmethod
    def verify_syntax(lex_tokens: list[LexicalBlock], expression: str):
        total_brackets = 0
        is_empty_brackets = False
        for i, token in enumerate(lex_tokens):
            if isinstance(token, OpenBracket):
                total_brackets += 1
                is_empty_brackets = True
                continue
            if isinstance(token, CloseBracket):
                if is_empty_brackets:
                    raise ValueError(f"Malformed expression: {expression}, there is an empty pairing of brackets at {i}")
                total_brackets -= 1
                continue

            is_empty_brackets = False

            if isinstance(token, LexBinaryOperation):
                if i + 1 == len(lex_tokens) or i == 0:
                    raise ValueError(f"Malformed expression: {expression}, binary operation '{token.char}', requires two inputs at position: {i}")

        if total_brackets > 0:
            raise ValueError(f"Malformed expression: {expression}, open brackets not closed")
        if total_brackets < 0:
            raise ValueError(f"Malformed expression: {expression}, too many closed brackets")

    @staticmethod
    def _reduce_operator(output_stack: list[FunctionASTNode], operator: LexicalBlock):
        if isinstance(operator, LexBinaryOperation):
            if len(output_stack) < 2:
                raise ValueError(f"Malformed expression: binary operation '{operator.char}' is missing operands")

            right = output_stack.pop()
            left = output_stack.pop()
            node = FunctionASTNode(operator)
            node.children.append(left)
            node.children.append(right)
            output_stack.append(node)
            return

        if isinstance(operator, LexFunction):
            raise ValueError("Function reductions require an explicit arity")

        raise ValueError(f"Unsupported operator type: {type(operator).__name__}")

    @staticmethod
    def _reduce_function(output_stack: list[FunctionASTNode], operator: LexFunction, arity: int):
        if arity < 1:
            raise ValueError(f"Malformed expression: function '{operator.char}' has no arguments")
        if len(output_stack) < arity:
            raise ValueError(f"Malformed expression: function '{operator.char}' is missing arguments")

        arguments = [output_stack.pop() for _ in range(arity)]
        arguments.reverse()

        node = FunctionASTNode(operator)
        node.children.extend(arguments)
        output_stack.append(node)

    @classmethod
    def from_mapping(cls, expression: str, namespace: Namespace, argument_variables: list[str]) -> FunctionAST:
        lex_tokens = cls.tokenise(expression, namespace, argument_variables)
        cls.verify_syntax(lex_tokens, expression)

        output_stack: list[FunctionASTNode] = []
        operator_stack: list[LexicalBlock] = []
        call_stack: list[_FunctionCallContext] = []

        def mark_argument_seen():
            if call_stack:
                call_stack[-1].has_argument = True

        def reduce_until_open_bracket():
            while operator_stack and not isinstance(operator_stack[-1], OpenBracket):
                cls._reduce_operator(output_stack, operator_stack.pop())

        for token in lex_tokens:
            if isinstance(token, (Literal, Identifier)):
                output_stack.append(FunctionASTNode(token))
                mark_argument_seen()
                continue

            if isinstance(token, LexFunction):
                operator_stack.append(token)
                continue

            if isinstance(token, OpenBracket):
                operator_stack.append(token)
                if len(operator_stack) >= 2 and isinstance(operator_stack[-2], LexFunction):
                    call_stack.append(_FunctionCallContext())
                continue

            if isinstance(token, Comma):
                if not call_stack:
                    raise ValueError(f"Malformed expression: {expression}, comma found outside of function argument list")

                reduce_until_open_bracket()
                if not call_stack[-1].has_argument:
                    raise ValueError(f"Malformed expression: {expression}, missing function argument before comma")

                call_stack[-1].arity += 1
                call_stack[-1].has_argument = False
                continue

            if isinstance(token, CloseBracket):
                if not operator_stack:
                    raise ValueError(f"Malformed expression: {expression}, mismatched brackets")

                reduce_until_open_bracket()
                if not operator_stack or not isinstance(operator_stack[-1], OpenBracket):
                    raise ValueError(f"Malformed expression: {expression}, mismatched brackets")

                operator_stack.pop()

                if operator_stack and isinstance(operator_stack[-1], LexFunction):
                    if not call_stack:
                        raise ValueError(f"Malformed expression: {expression}, internal function call state mismatch")

                    context = call_stack.pop()
                    if not context.has_argument:
                        raise ValueError(f"Malformed expression: {expression}, function call '{operator_stack[-1].char}' has an empty last argument")

                    function_token = operator_stack.pop()
                    cls._reduce_function(output_stack, function_token, context.arity)
                    mark_argument_seen()
                else:
                    mark_argument_seen()
                continue

            if isinstance(token, LexBinaryOperation):
                while (
                    operator_stack
                    and isinstance(operator_stack[-1], LexBinaryOperation)
                    and operator_stack[-1].precedence <= token.precedence
                ):
                    cls._reduce_operator(output_stack, operator_stack.pop())

                operator_stack.append(token)
                continue

        while operator_stack:
            operator = operator_stack.pop()
            if isinstance(operator, OpenBracket):
                raise ValueError(f"Malformed expression: {expression}, open brackets not closed")
            if isinstance(operator, LexFunction):
                raise ValueError(f"Malformed expression: function '{operator.char}' is missing an argument list")
            cls._reduce_operator(output_stack, operator)

        if len(output_stack) != 1:
            raise ValueError(f"Malformed expression: {expression}, too many literals remaining after parsing")

        return cls(output_stack[0])

    def __str__(self) -> str:
        def display_node(node: FunctionASTNode, indent: str = "") -> str:
            result = f"{indent}{node.actual}\n"
            for child in node.children:
                result += display_node(child, indent + "  ")
            return result

        return display_node(self.root)

    def __repr__(self) -> str:
        return f"FunctionAST({self.root})"
