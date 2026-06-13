from __future__ import annotations

from dataclasses import dataclass
from typing import overload

from Core.Function.BinaryOperations.Addition import Addition
from Core.Function.BinaryOperations.Division import Division
from Core.Function.BinaryOperations.Negation import Negation
from Core.Function.BinaryOperations.Multiplication import Multiplication
from Core.Function.BinaryOperations.Subtraction import Subtraction
from Core.Function.FunctionInterpreter.LexicalBlocks.LexBinaryOperation import LexBinaryOperation
from Core.Function.FunctionInterpreter.LexicalBlocks.LexFunction import LexFunction
from Core.Function.FunctionInterpreter.LexicalBlocks.LexLiterals import Comma, CloseBracket, Identifier, Literal, OpenBracket
from Core.Function.FunctionInterpreter.LexicalBlocks.LexicalBlock import LexicalBlock
from Core.Function.FunctionInterpreter.LexicalBlocks.LexUnaryOperation import LexUnaryOperation
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

    @children.setter
    def children(self, value: list[FunctionASTNode]):
        self._children = value

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
    def extract_coefficient(node) -> tuple[float, FunctionASTNode]:
        if isinstance(node.actual, LexUnaryOperation) and isinstance(node.actual.operation, Negation):
            coeff, base = FunctionAST.extract_coefficient(node.children[0])
            return -coeff, base

        # x -> (1, x)
        if isinstance(node.actual, Identifier):
            return 1, node

        # 3*x*y -> (3, x*y)
        if (
                isinstance(node.actual, LexBinaryOperation)
                and isinstance(node.actual.operation, Multiplication)
        ):
            factors = FunctionAST._flatten_associative(node, node.actual.operation)
            coefficient = 1.0
            remaining_factors: list[FunctionASTNode] = []

            for factor in factors:
                if isinstance(factor.actual, Literal):
                    coefficient *= float(factor.actual.char)
                else:
                    remaining_factors.append(factor)

            if not remaining_factors:
                return coefficient, node

            if len(remaining_factors) == 1:
                return coefficient, remaining_factors[0]

            return coefficient, FunctionAST._build_binary_chain(node.actual, remaining_factors)

        if (
            isinstance(node.actual, LexBinaryOperation)
            and isinstance(node.actual.operation, Division)
        ):
            numerator, denominator = node.children
            if isinstance(denominator.actual, Literal):
                denominator_value = float(denominator.actual.char)
                if denominator_value != 0:
                    return 1 / denominator_value, numerator

        # everything else treated as coefficient 1
        return 1, node

    @staticmethod
    def _flatten_associative(node, operation) -> list[FunctionASTNode]:
        result = []

        if (
                isinstance(node.actual, LexBinaryOperation)
                and node.actual.operation == operation
                and operation.associative
        ):
            for child in node.children:
                result.extend(
                    FunctionAST._flatten_associative(child, operation)
                )
        else:
            result.append(node)

        return result

    @staticmethod
    def _collect_signed_terms(node: FunctionASTNode, sign: float = 1.0) -> list[tuple[float, FunctionASTNode]]:
        if isinstance(node.actual, LexUnaryOperation) and isinstance(node.actual.operation, Negation):
            return FunctionAST._collect_signed_terms(node.children[0], -sign)

        if isinstance(node.actual, LexBinaryOperation):
            if isinstance(node.actual.operation, Addition):
                terms: list[tuple[float, FunctionASTNode]] = []
                for child in node.children:
                    terms.extend(FunctionAST._collect_signed_terms(child, sign))
                return terms

            if isinstance(node.actual.operation, Subtraction):
                left, right = node.children
                return (
                    FunctionAST._collect_signed_terms(left, sign)
                    + FunctionAST._collect_signed_terms(right, -sign)
                )

        return [(sign, node)]

    @staticmethod
    def _clone_node(node: FunctionASTNode) -> FunctionASTNode:
        cloned = FunctionASTNode(node.actual)
        cloned.children = [FunctionAST._clone_node(child) for child in node.children]
        return cloned

    @staticmethod
    def _literal_node(value: float) -> FunctionASTNode:
        if float(value).is_integer():
            return FunctionASTNode(Literal(str(int(value))))
        return FunctionASTNode(Literal(str(value)))

    @staticmethod
    def _signature(node: FunctionASTNode) -> str:
        if isinstance(node.actual, Literal):
            return f"L:{node.actual.char}"
        if isinstance(node.actual, Identifier):
            return f"I:{node.actual.char}"
        if isinstance(node.actual, LexFunction):
            child_signatures = ",".join(FunctionAST._signature(child) for child in node.children)
            return f"F:{node.actual.char}({child_signatures})"
        if isinstance(node.actual, LexUnaryOperation):
            return f"UO:{node.actual.char}({FunctionAST._signature(node.children[0])})"
        if isinstance(node.actual, LexBinaryOperation):
            child_signatures = [FunctionAST._signature(child) for child in node.children]
            if node.actual.operation.commutative:
                child_signatures.sort()
            return f"B:{node.actual.char}({','.join(child_signatures)})"
        return f"U:{type(node.actual).__name__}"

    @staticmethod
    def _build_binary_chain(operator: LexBinaryOperation, children: list[FunctionASTNode]) -> FunctionASTNode:
        if not children:
            raise ValueError("Cannot build an empty binary chain")
        if len(children) == 1:
            return children[0]

        root = FunctionASTNode(operator)
        root.children = [children[0], children[1]]
        for child in children[2:]:
            new_root = FunctionASTNode(operator)
            new_root.children = [root, child]
            root = new_root
        return root

    @staticmethod
    def _build_add_chain(children: list[FunctionASTNode]) -> FunctionASTNode:
        return FunctionAST._build_binary_chain(LexBinaryOperation("+", Addition().precedence, Addition()), children)

    @staticmethod
    def _make_binary_node(operation, left: FunctionASTNode, right: FunctionASTNode) -> FunctionASTNode:
        node = FunctionASTNode(LexBinaryOperation(operation.name, operation.precedence, operation))
        node.children = [left, right]
        return node

    @staticmethod
    def _make_unary_node(operation, child: FunctionASTNode) -> FunctionASTNode:
        node = FunctionASTNode(LexUnaryOperation("-", operation.precedence, operation))
        node.children = [child]
        return node

    def evaluate(self, namespace: Namespace) -> float:
        if isinstance(self.root.actual, Literal):
            return float(self.root.actual.char)
        if isinstance(self.root.actual, Identifier):
            if self.root.actual.char not in namespace.variables:
                raise ValueError(f"Undefined variable: {self.root.actual.char}")
            return namespace.variables[self.root.actual.char]
        if isinstance(self.root.actual, LexFunction):
            function = self.root.actual.operation
            arguments = [FunctionAST(child).evaluate(namespace) for child in self.root.children]
            return function.evaluate(*arguments)
        if isinstance(self.root.actual, LexUnaryOperation):
            operation = self.root.actual.operation
            argument = FunctionAST(self.root.children[0]).evaluate(namespace)
            return operation.calculate(argument)
        if isinstance(self.root.actual, LexBinaryOperation):
            operation = self.root.actual.operation
            arguments = [FunctionAST(child).evaluate(namespace) for child in self.root.children]
            return operation.calculate(*arguments)

        raise ValueError(f"Unsupported AST node type: {type(self.root.actual).__name__}")

    @staticmethod
    def simplify(ast: FunctionAST) -> FunctionAST:
        def simplify_node(node: FunctionASTNode) -> FunctionASTNode:
            if isinstance(node.actual, (Literal, Identifier)):
                return FunctionAST._clone_node(node)

            if isinstance(node.actual, LexFunction):
                simplified_children = [simplify_node(child) for child in node.children]
                if simplified_children and all(isinstance(child.actual, Literal) for child in simplified_children):
                    values = [float(child.actual.char) for child in simplified_children]
                    result = node.actual.operation.evaluate(*values)
                    return FunctionAST._literal_node(result)

                new_node = FunctionASTNode(node.actual)
                new_node.children = simplified_children
                return new_node

            if isinstance(node.actual, LexUnaryOperation):
                simplified_child = simplify_node(node.children[0])
                if isinstance(simplified_child.actual, LexUnaryOperation):
                    return FunctionAST._clone_node(simplified_child.children[0])
                if isinstance(simplified_child.actual, Literal):
                    return FunctionAST._literal_node(-float(simplified_child.actual.char))

                new_node = FunctionASTNode(node.actual)
                new_node.children = [simplified_child]
                return new_node

            if isinstance(node.actual, LexBinaryOperation):
                operation = node.actual.operation
                simplified_children = [simplify_node(child) for child in node.children]

                if isinstance(operation, (Addition, Subtraction)):
                    additive_node = FunctionASTNode(node.actual)
                    additive_node.children = simplified_children
                    flattened = FunctionAST._collect_signed_terms(additive_node)

                    literal_total = 0.0
                    grouped: dict[str, tuple[float, FunctionASTNode]] = {}
                    ordered_terms: list[FunctionASTNode] = []

                    for sign, term in flattened:
                        if isinstance(term.actual, Literal):
                            literal_total += sign * float(term.actual.char)
                            continue

                        coeff, base = FunctionAST.extract_coefficient(term)
                        base = simplify_node(base)
                        coeff *= sign
                        key = FunctionAST._signature(base)
                        if key in grouped:
                            existing_coeff, existing_base = grouped[key]
                            grouped[key] = (existing_coeff + coeff, existing_base)
                        else:
                            grouped[key] = (coeff, base)

                    if literal_total != 0:
                        ordered_terms.append(FunctionAST._literal_node(literal_total))

                    for coeff, base in grouped.values():
                        if coeff == 0:
                            continue
                        if coeff == 1:
                            ordered_terms.append(base)
                            continue
                        if coeff == -1:
                            ordered_terms.append(FunctionAST._make_unary_node(Negation(), base))
                            continue
                        coeff_node = FunctionAST._literal_node(coeff)
                        ordered_terms.append(FunctionAST._make_binary_node(Multiplication(), coeff_node, base))

                    ordered_terms.sort(key=FunctionAST._signature)

                    if not ordered_terms:
                        return FunctionAST._literal_node(0)
                    if len(ordered_terms) == 1:
                        return ordered_terms[0]

                    return FunctionAST._build_add_chain(ordered_terms)

                if isinstance(operation, Multiplication):
                    flattened: list[FunctionASTNode] = []
                    for child in simplified_children:
                        flattened.extend(FunctionAST._flatten_associative(child, operation))

                    coefficient = 1.0
                    factors: list[FunctionASTNode] = []

                    for factor in flattened:
                        if isinstance(factor.actual, Literal):
                            value = float(factor.actual.char)
                            if value == 0:
                                return FunctionASTNode(Literal("0"))
                            coefficient *= value
                            continue

                        factors.append(factor)

                    if coefficient == 0:
                        return FunctionAST._literal_node(0)

                    if coefficient != 1 or not factors:
                        factors.insert(0, FunctionAST._literal_node(coefficient))

                    factors.sort(key=FunctionAST._signature)

                    if len(factors) == 1:
                        return factors[0]

                    return FunctionAST._build_binary_chain(node.actual, factors)

                if isinstance(operation, (Subtraction, Division)):
                    if len(simplified_children) == 2:
                        right = simplified_children[1]
                        if isinstance(right.actual, Literal) and float(right.actual.char) == operation.identity:
                            return simplified_children[0]

                if all(isinstance(child.actual, Literal) for child in simplified_children):
                    values = [float(child.actual.char) for child in simplified_children]
                    result = operation.calculate(*values)
                    return FunctionAST._literal_node(result)

                if operation.associative:
                    flattened = []
                    for child in simplified_children:
                        flattened.extend(FunctionAST._flatten_associative(child, operation))
                    simplified_children = flattened

                if operation.commutative:
                    simplified_children.sort(key=FunctionAST._signature)

                identity = operation.identity
                filtered_children = []
                for index, child in enumerate(simplified_children):
                    if (
                        operation.commutative
                        and operation.associative
                        and isinstance(child.actual, Literal)
                        and float(child.actual.char) == identity
                    ):
                        continue
                    if (
                        not operation.commutative
                        and not operation.associative
                        and index == 1
                        and isinstance(child.actual, Literal)
                        and float(child.actual.char) == identity
                    ):
                        continue
                    filtered_children.append(child)

                if not filtered_children:
                    return FunctionAST._literal_node(identity)
                if len(filtered_children) == 1:
                    return filtered_children[0]

                return FunctionAST._build_binary_chain(node.actual, filtered_children)

            new_node = FunctionASTNode(node.actual)
            new_node.children = [simplify_node(child) for child in node.children]
            return new_node

        return FunctionAST(simplify_node(ast.root))

    def simplify_ast(self) -> FunctionAST:
        return FunctionAST.simplify(self)

    @staticmethod
    def tokenise(expression: str, namespace: Namespace, argument_variables: list[str]) -> list[LexicalBlock]:
        tokens: list[LexicalBlock] = []
        i = 0
        expecting_operand = True

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

                if namespace.is_in_function_namespace(name):
                    lookahead = i
                    while lookahead < len(expression) and expression[lookahead].isspace():
                        lookahead += 1
                    if lookahead >= len(expression) or expression[lookahead] != "(":
                        raise ValueError(f"Malformed function expression: expected '(' after function name '{name}'")
                    tokens.append(LexFunction(name, namespace.functions[name]))
                    expecting_operand = True
                    continue

                raise ValueError(f"Unknown identifier or function name: {name}")

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

        if isinstance(operator, LexUnaryOperation):
            if len(output_stack) < 1:
                raise ValueError(f"Malformed expression: unary operation '{operator.char}' is missing an operand")

            child = output_stack.pop()
            node = FunctionASTNode(operator)
            node.children.append(child)
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

    @staticmethod
    def _check_function_arguments(ast: FunctionAST):
        if isinstance(ast.root.actual, LexFunction):
            no_expected_arguments = ast.root.actual.operation.get_amount_of_arguments()
            given_args = len(ast.root.children)
            if not given_args == no_expected_arguments:
                raise ValueError(f"Malformed expression: function '{ast.root.actual.char}' does not have expected arguments")
        for child in ast.root.children:
            FunctionAST._check_function_arguments(FunctionAST(child))

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

        def reduce_prefix_unary():
            while operator_stack and isinstance(operator_stack[-1], LexUnaryOperation):
                cls._reduce_operator(output_stack, operator_stack.pop())

        for token in lex_tokens:
            if isinstance(token, (Literal, Identifier)):
                output_stack.append(FunctionASTNode(token))
                mark_argument_seen()
                reduce_prefix_unary()
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

        output = cls(output_stack[0])
        FunctionAST._check_function_arguments(output)
        return output

    def get_raw_expression(self) -> str:
        def build_expression(node: FunctionASTNode) -> str:
            if isinstance(node.actual, Literal):
                return node.actual.char
            if isinstance(node.actual, Identifier):
                return node.actual.char
            if isinstance(node.actual, LexFunction):
                args = ",".join(build_expression(child) for child in node.children)
                return f"{node.actual.char}({args})"
            if isinstance(node.actual, LexUnaryOperation):
                return f"({node.actual.char}{build_expression(node.children[0])})"
            if isinstance(node.actual, LexBinaryOperation):
                left = build_expression(node.children[0])
                right = build_expression(node.children[1])
                return f"({left}{node.actual.char}{right})"
            raise ValueError(f"Unsupported AST node type: {type(node.actual).__name__}")

        return build_expression(self.root)

    def __str__(self) -> str:
        def display_node(node: FunctionASTNode, indent: str = "") -> str:
            result = f"{indent}{node.actual}\n"
            for child in node.children:
                result += display_node(child, indent + "  ")
            return result

        return display_node(self.root)

    def __repr__(self) -> str:
        return f"FunctionAST({self.root})"
