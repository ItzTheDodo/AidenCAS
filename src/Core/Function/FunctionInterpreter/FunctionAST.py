from __future__ import annotations

from dataclasses import dataclass

from Core.Function.BinaryOperations.Negation import Negation
from Core.Function.FunctionInterpreter.ASTNodes import (
    BinaryOperationNode,
    ExpressionNode,
    FunctionCallNode,
    IdentifierNode,
    LiteralNode,
    _literal,
    _substitute,
    SimplificationContext,
    UnaryOperationNode,
)
from Core.Function.FunctionInterpreter.LexicalBlocks.LexBinaryOperation import LexBinaryOperation
from Core.Function.FunctionInterpreter.LexicalBlocks.LexFunction import LexFunction
from Core.Function.FunctionInterpreter.LexicalBlocks.LexLiterals import Comma, CloseBracket, Identifier, Infinity, Literal, MatrixLiteral, OpenBracket
from Core.Function.FunctionInterpreter.LexicalBlocks.LexicalBlock import LexicalBlock
from Core.Function.FunctionInterpreter.LexicalBlocks.LexUnaryOperation import LexUnaryOperation
from Core.Namespace.Namespace import Namespace


@dataclass
class _FunctionCallContext:
    """Tracks commas/arguments while parsing a single function call."""
    arity: int = 1
    has_argument: bool = False


class FunctionAST:
    """Parser and wrapper around the immutable function-expression tree."""

    def __init__(self, root: ExpressionNode):
        self._root = root

    @property
    def root(self) -> ExpressionNode:
        return self._root

    def set_root(self, node: ExpressionNode):
        self._root = node

    @staticmethod
    def tokenise(expression: str, namespace: Namespace, argument_variables: list[str]) -> list[LexicalBlock]:
        """Turn a source expression into lexical blocks."""
        tokens: list[LexicalBlock] = []
        i = 0
        expecting_operand = True

        while i < len(expression):
            character = expression[i]

            if character.isspace():
                i += 1
                continue

            if character.isdigit() or (character == "." and i + 1 < len(expression) and expression[i + 1].isdigit()):
                start = i
                seen_decimal_point = False
                while i < len(expression):
                    current = expression[i]
                    if current.isdigit():
                        i += 1
                        continue
                    if current == "." and not seen_decimal_point:
                        seen_decimal_point = True
                        i += 1
                        continue
                    break

                tokens.append(Literal(expression[start:i]))
                expecting_operand = False
                continue

            if character.isalpha() or character in {"_", "|"}:
                start = i
                i += 1
                while i < len(expression) and (expression[i].isalnum() or expression[i] in {"_", "|"}):
                    i += 1

                name = expression[start:i]
                if name in argument_variables:
                    tokens.append(Identifier(name))
                    expecting_operand = False
                    continue

                if name in {"inf", "infinity"}:
                    tokens.append(Literal("inf"))
                    expecting_operand = False
                    continue

                if namespace.is_in_function_namespace(name):
                    lookahead = i
                    while lookahead < len(expression) and expression[lookahead].isspace():
                        lookahead += 1
                    if lookahead >= len(expression) or expression[lookahead] != "(":
                        raise ValueError(f"Malformed function expression: expected '(' after function name '{name}'")
                    tokens.append(LexFunction(name, namespace.functions[name]))
                    expecting_operand = True
                    continue

                lookahead = i
                while lookahead < len(expression) and expression[lookahead].isspace():
                    lookahead += 1
                if lookahead < len(expression) and expression[lookahead] == "(":
                    namespace.reserve_function(name)
                    tokens.append(LexFunction(name, namespace.functions[name]))
                    expecting_operand = True
                    continue

                tokens.append(Identifier(name))
                expecting_operand = False
                continue

            if character == "(":
                tokens.append(OpenBracket(character))
                i += 1
                expecting_operand = True
                continue

            if character == ")":
                tokens.append(CloseBracket(character))
                i += 1
                expecting_operand = False
                continue

            if character == ",":
                tokens.append(Comma(character))
                i += 1
                expecting_operand = True
                continue

            if character == "[":
                start = i
                depth = 0
                while i < len(expression):
                    current = expression[i]
                    if current == "[":
                        depth += 1
                    elif current == "]":
                        depth -= 1
                        if depth == 0:
                            i += 1
                            tokens.append(MatrixLiteral(expression[start:i]))
                            expecting_operand = False
                            break
                    i += 1
                else:
                    raise ValueError(f"Malformed expression: {expression}, matrix literal not closed")
                continue

            if character == "-" and expecting_operand:
                tokens.append(LexUnaryOperation(character, Negation().precedence, Negation()))
                i += 1
                continue

            if namespace.is_in_binary_operation_namespace(character):
                binary_operation = namespace.binary_operations[character]
                tokens.append(LexBinaryOperation(character, binary_operation.precedence, binary_operation))
                i += 1
                expecting_operand = True
                continue

            raise ValueError(f"Unexpected character '{character}' in expression: {expression}")

        return tokens

    @staticmethod
    def verify_syntax(lex_tokens: list[LexicalBlock], expression: str):
        """Run lightweight bracket/operator validation before parsing."""
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
    def _reduce_operator(output_stack: list[ExpressionNode], operator: LexicalBlock):
        """Pop operands from the value stack and build a node for an operator."""
        if isinstance(operator, LexBinaryOperation):
            if len(output_stack) < 2:
                raise ValueError(f"Malformed expression: binary operation '{operator.char}' is missing operands")
            right = output_stack.pop()
            left = output_stack.pop()
            output_stack.append(BinaryOperationNode(operator.operation, left, right))
            return

        if isinstance(operator, LexUnaryOperation):
            if len(output_stack) < 1:
                raise ValueError(f"Malformed expression: unary operation '{operator.char}' is missing an operand")
            child = output_stack.pop()
            output_stack.append(UnaryOperationNode(operator.operation, child))
            return

        raise ValueError(f"Unsupported operator type: {type(operator).__name__}")

    @staticmethod
    def _reduce_function(output_stack: list[ExpressionNode], operator: LexFunction, arity: int):
        """Pop function arguments from the stack and build a call node."""
        if arity < 1:
            raise ValueError(f"Malformed expression: function '{operator.char}' has no arguments")
        if len(output_stack) < arity:
            raise ValueError(f"Malformed expression: function '{operator.char}' is missing arguments")

        arguments = [output_stack.pop() for _ in range(arity)]
        arguments.reverse()
        if hasattr(operator.operation, "build_node"):
            output_stack.append(operator.operation.build_node(tuple(arguments)))
        else:
            output_stack.append(FunctionCallNode(operator.operation, tuple(arguments)))

    @staticmethod
    def _check_function_arguments(node: ExpressionNode):
        """Ensure the parsed call arity matches the referenced function."""
        if isinstance(node, FunctionCallNode):
            if not getattr(node.function, "is_resolved", True):
                return
            if len(node.arguments) != node.function.get_amount_of_arguments():
                raise ValueError(f"Malformed expression: function '{node.function.name}' does not have expected arguments")
        for child in node.children:
            FunctionAST._check_function_arguments(child)

    @staticmethod
    def _split_top_level(text: str, delimiter: str = ",") -> list[str]:
        parts: list[str] = []
        current: list[str] = []
        paren_depth = 0
        bracket_depth = 0
        for char in text:
            if char == "(":
                paren_depth += 1
            elif char == ")":
                paren_depth -= 1
            elif char == "[":
                bracket_depth += 1
            elif char == "]":
                bracket_depth -= 1

            if char == delimiter and paren_depth == 0 and bracket_depth == 0:
                part = "".join(current).strip()
                if part:
                    parts.append(part)
                current = []
                continue

            current.append(char)

        if paren_depth != 0 or bracket_depth != 0:
            raise ValueError("Malformed matrix literal")

        tail = "".join(current).strip()
        if tail:
            parts.append(tail)
        return parts

    @classmethod
    def _parse_matrix_literal(cls, literal: str) -> LiteralNode:
        inner = literal.strip()
        if not inner.startswith("[") or not inner.endswith("]"):
            raise ValueError(f"Malformed matrix literal: {literal}")

        inner = inner[1:-1].strip()
        if not inner:
            raise ValueError("Matrix literals cannot be empty")

        row_sources = cls._split_top_level(inner)
        if "[" not in inner and "]" not in inner:
            row_sources = [inner]

        rows: list[tuple[float, ...]] = []
        expected_width: int | None = None
        for row_source in row_sources:
            row_text = row_source.strip()
            if "[" in inner or "]" in inner:
                if not row_text.startswith("[") or not row_text.endswith("]"):
                    raise ValueError(f"Malformed matrix literal row: {row_source}")
                row_text = row_text[1:-1].strip()
            entries = [entry.strip() for entry in cls._split_top_level(row_text)]
            if not entries:
                raise ValueError("Matrix rows cannot be empty")

            row: list[float] = []
            for entry in entries:
                if entry in {"inf", "infinity"}:
                    row.append(float("inf"))
                else:
                    row.append(float(entry))

            if expected_width is None:
                expected_width = len(row)
            elif len(row) != expected_width:
                raise ValueError("Matrix rows must all have the same length")

            rows.append(tuple(row))

        return _literal(tuple(rows))

    @classmethod
    def from_mapping(cls, expression: str, namespace: Namespace, argument_variables: list[str]) -> FunctionAST:
        """Parse an expression string into an AST."""
        lex_tokens = cls.tokenise(expression, namespace, argument_variables)
        cls.verify_syntax(lex_tokens, expression)

        output_stack: list[ExpressionNode] = []
        operator_stack: list[LexicalBlock] = []
        call_stack: list[_FunctionCallContext] = []

        def mark_argument_seen():
            """Record that the current call context has consumed an argument."""
            if call_stack:
                call_stack[-1].has_argument = True

        def reduce_until_open_bracket():
            """Collapse stacked operators until the current argument boundary."""
            while operator_stack and not isinstance(operator_stack[-1], OpenBracket):
                cls._reduce_operator(output_stack, operator_stack.pop())

        def reduce_prefix_unary():
            """Apply any pending unary operators to the most recent operand."""
            while operator_stack and isinstance(operator_stack[-1], LexUnaryOperation):
                cls._reduce_operator(output_stack, operator_stack.pop())

        for token in lex_tokens:
            if isinstance(token, MatrixLiteral):
                output_stack.append(cls._parse_matrix_literal(token.char))
                mark_argument_seen()
                reduce_prefix_unary()
                continue

            if isinstance(token, (Literal, Identifier)):
                if isinstance(token, Literal):
                    if token.char in {"inf", "infinity"}:
                        output_stack.append(LiteralNode(float("inf")))
                    else:
                        output_stack.append(LiteralNode(float(token.char)))
                else:
                    output_stack.append(IdentifierNode(token.char))
                mark_argument_seen()
                reduce_prefix_unary()
                continue

            if isinstance(token, LexFunction):
                operator_stack.append(token)
                continue

            if isinstance(token, OpenBracket):
                operator_stack.append(token)
                if len(operator_stack) >= 2:
                    previous = operator_stack[-2]
                    if isinstance(previous, LexFunction):
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
                    reduce_prefix_unary()
                else:
                    mark_argument_seen()
                    reduce_prefix_unary()
                continue

            if isinstance(token, LexUnaryOperation):
                operator_stack.append(token)
                continue

            if isinstance(token, LexBinaryOperation):
                reduce_prefix_unary()
                while (
                    operator_stack
                    and isinstance(operator_stack[-1], LexBinaryOperation)
                    and (
                        operator_stack[-1].precedence < token.precedence
                        or (
                            operator_stack[-1].precedence == token.precedence
                            and not token.operation.right_associative
                        )
                    )
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

        output = cls(output_stack[0])
        cls._check_function_arguments(output.root)
        return output

    def simplify_ast(self, context: SimplificationContext | None = None) -> FunctionAST:
        """Return a simplified copy of this AST."""
        return FunctionAST(self.root.simplify(context if context is not None else SimplificationContext()))

    def canonical_simplify_ast(self) -> FunctionAST:
        """Return the AST in canonical simplified form."""
        return self.simplify_ast(SimplificationContext())

    def substitute(self, mapping: dict[str, ExpressionNode]) -> FunctionAST:
        """Return a new AST with identifiers replaced by expression trees."""
        return FunctionAST(_substitute(self.root, mapping))

    def derivative(self, variable: str) -> FunctionAST:
        """Return a new AST representing the derivative of this AST with respect to a variable."""
        return FunctionAST(self.root.derivative(variable).simplify(SimplificationContext()))

    @staticmethod
    def simplify(ast: FunctionAST) -> FunctionAST:
        """Convenience wrapper for callers that still use the old API."""
        return ast.simplify_ast()

    def evaluate(self, namespace: Namespace) -> float:
        """Evaluate the expression against a namespace of variables."""
        return self.root.evaluate(namespace)

    def get_raw_expression(self) -> str:
        """Render the tree back to a parenthesized expression string."""
        return self.root.to_expression()

    def __str__(self) -> str:
        return self.root.render()

    def __repr__(self) -> str:
        return f"FunctionAST({self.root})"
