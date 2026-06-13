from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from Core.Function.BinaryOperations.Addition import Addition
from Core.Function.BinaryOperations.BinaryOperation import BinaryOperation
from Core.Function.BinaryOperations.Division import Division
from Core.Function.BinaryOperations.Negation import Negation
from Core.Function.BinaryOperations.Multiplication import Multiplication
from Core.Function.BinaryOperations.Subtraction import Subtraction

if TYPE_CHECKING:
    from Core.Function.FunctionInterpreter.Function import Function
    from Core.Function.FunctionInterpreter.Simplifier import SimplificationContext
    from Core.Namespace.Namespace import Namespace


def _format_number(value: float) -> str:
    """Render numeric values without trailing `.0` when possible."""
    return str(int(value)) if float(value).is_integer() else str(value)


def _literal(value: float) -> LiteralNode:
    return LiteralNode(value)


def _unary(operation: Negation, child: ExpressionNode) -> UnaryOperationNode:
    return UnaryOperationNode(operation, child)


def _binary(operation: BinaryOperation, left: ExpressionNode, right: ExpressionNode) -> BinaryOperationNode:
    return BinaryOperationNode(operation, left, right)


def _build_binary_chain(operation: BinaryOperation, children: tuple[ExpressionNode, ...]) -> ExpressionNode:
    if not children:
        raise ValueError("Cannot build an empty binary chain")
    if len(children) == 1:
        return children[0]

    node: ExpressionNode = BinaryOperationNode(operation, children[0], children[1])
    for child in children[2:]:
        node = BinaryOperationNode(operation, node, child)
    return node


def _flatten_associative(node: ExpressionNode, operation: BinaryOperation) -> tuple[ExpressionNode, ...]:
    if isinstance(node, BinaryOperationNode) and node.operation.name == operation.name and node.operation.associative:
        flattened: list[ExpressionNode] = []
        for child in node.children:
            flattened.extend(_flatten_associative(child, operation))
        return tuple(flattened)
    return (node,)


def _signature(node: ExpressionNode) -> str:
    if isinstance(node, LiteralNode):
        return f"L:{_format_number(node.value)}"
    if isinstance(node, IdentifierNode):
        return f"I:{node.name}"
    if isinstance(node, UnaryOperationNode):
        return f"U:{node.operation.name}({_signature(node.child)})"
    if isinstance(node, FunctionCallNode):
        args = ",".join(_signature(arg) for arg in node.arguments)
        return f"F:{node.function.name}({args})"
    if isinstance(node, BinaryOperationNode):
        child_signatures = [_signature(node.left), _signature(node.right)]
        if node.operation.commutative:
            child_signatures.sort()
        return f"B:{node.operation.name}({','.join(child_signatures)})"
    return type(node).__name__


def _extract_coefficient(node: ExpressionNode) -> tuple[float, ExpressionNode]:
    if isinstance(node, UnaryOperationNode) and isinstance(node.operation, Negation):
        coeff, base = _extract_coefficient(node.child)
        return -coeff, base

    if isinstance(node, IdentifierNode):
        return 1.0, node

    if isinstance(node, BinaryOperationNode) and isinstance(node.operation, Multiplication):
        factors = _flatten_associative(node, node.operation)
        coefficient = 1.0
        remaining: list[ExpressionNode] = []
        for factor in factors:
            if isinstance(factor, LiteralNode):
                coefficient *= factor.value
            else:
                remaining.append(factor)
        if not remaining:
            return coefficient, node
        if len(remaining) == 1:
            return coefficient, remaining[0]
        return coefficient, _build_binary_chain(node.operation, tuple(remaining))

    if isinstance(node, BinaryOperationNode) and isinstance(node.operation, Division):
        numerator, denominator = node.left, node.right
        if isinstance(denominator, LiteralNode) and denominator.value != 0:
            return 1 / denominator.value, numerator

    return 1.0, node


def _collect_signed_terms(node: ExpressionNode, sign: float = 1.0) -> tuple[tuple[float, ExpressionNode], ...]:
    if isinstance(node, UnaryOperationNode) and isinstance(node.operation, Negation):
        return _collect_signed_terms(node.child, -sign)

    if isinstance(node, BinaryOperationNode):
        if isinstance(node.operation, Addition):
            terms: list[tuple[float, ExpressionNode]] = []
            for child in node.children:
                terms.extend(_collect_signed_terms(child, sign))
            return tuple(terms)

        if isinstance(node.operation, Subtraction):
            return _collect_signed_terms(node.left, sign) + _collect_signed_terms(node.right, -sign)

    return ((sign, node),)


@dataclass(frozen=True)
class SimplificationContext:
    """Flags that control which simplification rules are active."""
    fold_constants: bool = True
    simplify_unary: bool = True
    normalize_addition: bool = True
    normalize_multiplication: bool = True
    eliminate_identities: bool = True


class ExpressionNode(ABC):
    """Base class for immutable AST nodes."""

    @property
    @abstractmethod
    def children(self) -> tuple[ExpressionNode, ...]:
        raise NotImplementedError

    @abstractmethod
    def simplify(self, context: SimplificationContext) -> ExpressionNode:
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, namespace: Namespace) -> float:
        raise NotImplementedError

    @abstractmethod
    def to_expression(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def signature(self) -> str:
        raise NotImplementedError

    def render(self, indent: str = "") -> str:
        """Return a tree-formatted representation for debugging."""
        lines = [f"{indent}{self}"]
        for child in self.children:
            lines.append(child.render(indent + "  "))
        return "\n".join(lines)


@dataclass(frozen=True)
class LiteralNode(ExpressionNode):
    """Numeric constant leaf node."""
    value: float

    @property
    def children(self) -> tuple[ExpressionNode, ...]:
        return ()

    def simplify(self, context: SimplificationContext) -> ExpressionNode:
        """Literals are already in simplest form."""
        return self

    def evaluate(self, namespace: Namespace) -> float:
        return self.value

    def to_expression(self) -> str:
        return _format_number(self.value)

    def signature(self) -> str:
        return f"L:{self.to_expression()}"

    def __str__(self) -> str:
        return f"Literal({self.to_expression()})"


@dataclass(frozen=True)
class IdentifierNode(ExpressionNode):
    """Variable reference leaf node."""
    name: str

    @property
    def children(self) -> tuple[ExpressionNode, ...]:
        return ()

    def simplify(self, context: SimplificationContext) -> ExpressionNode:
        """Identifiers are simplified by surrounding rules, not directly."""
        return self

    def evaluate(self, namespace: Namespace) -> float:
        if self.name not in namespace.variables:
            raise ValueError(f"Undefined variable: {self.name}")
        return namespace.variables[self.name]

    def to_expression(self) -> str:
        return self.name

    def signature(self) -> str:
        return f"I:{self.name}"

    def __str__(self) -> str:
        return f"Identifier({self.name})"


@dataclass(frozen=True)
class UnaryOperationNode(ExpressionNode):
    """Prefix unary operation node."""
    operation: Negation
    child: ExpressionNode

    @property
    def children(self) -> tuple[ExpressionNode, ...]:
        return (self.child,)

    def simplify(self, context: SimplificationContext) -> ExpressionNode:
        """Simplify the child, then apply unary-specific rules."""
        child = self.child.simplify(context)

        if context.simplify_unary and isinstance(child, UnaryOperationNode) and isinstance(child.operation, Negation):
            return child.child

        if context.fold_constants and isinstance(child, LiteralNode):
            return _literal(-child.value)

        return UnaryOperationNode(self.operation, child)

    def evaluate(self, namespace: Namespace) -> float:
        return self.operation.calculate(self.child.evaluate(namespace))

    def to_expression(self) -> str:
        return f"(-{self.child.to_expression()})"

    def signature(self) -> str:
        return f"U:{self.operation.name}({self.child.signature()})"

    def __str__(self) -> str:
        return f"Unary({self.operation.name})"


@dataclass(frozen=True)
class FunctionCallNode(ExpressionNode):
    """Function invocation node with immutable argument tuple."""
    function: Function
    arguments: tuple[ExpressionNode, ...]

    @property
    def children(self) -> tuple[ExpressionNode, ...]:
        return self.arguments

    def simplify(self, context: SimplificationContext) -> ExpressionNode:
        """Simplify arguments before optionally folding constant calls."""
        args = tuple(arg.simplify(context) for arg in self.arguments)
        if context.fold_constants and args and all(isinstance(arg, LiteralNode) for arg in args):
            return _literal(self.function.evaluate(*[arg.value for arg in args]))
        return FunctionCallNode(self.function, args)

    def evaluate(self, namespace: Namespace) -> float:
        return self.function.evaluate(*[arg.evaluate(namespace) for arg in self.arguments])

    def to_expression(self) -> str:
        return f"{self.function.name}({','.join(arg.to_expression() for arg in self.arguments)})"

    def signature(self) -> str:
        return f"F:{self.function.name}({','.join(arg.signature() for arg in self.arguments)})"

    def __str__(self) -> str:
        return f"Call({self.function.name})"


@dataclass(frozen=True)
class BinaryOperationNode(ExpressionNode):
    """Binary operator node for arithmetic and function algebra."""
    operation: BinaryOperation
    left: ExpressionNode
    right: ExpressionNode

    @property
    def children(self) -> tuple[ExpressionNode, ...]:
        return (self.left, self.right)

    def simplify(self, context: SimplificationContext) -> ExpressionNode:
        """Simplify children first, then apply operator-specific rules."""
        left = self.left.simplify(context)
        right = self.right.simplify(context)

        if context.fold_constants and isinstance(left, LiteralNode) and isinstance(right, LiteralNode):
            return _literal(self.operation.calculate(left.value, right.value))

        if isinstance(self.operation, (Addition, Subtraction)) and context.normalize_addition:
            additive = BinaryOperationNode(self.operation, left, right)
            signed_terms = _collect_signed_terms(additive)

            literal_total = 0.0
            grouped: dict[str, tuple[float, ExpressionNode]] = {}
            ordered_terms: list[ExpressionNode] = []

            for sign, term in signed_terms:
                if isinstance(term, LiteralNode):
                    literal_total += sign * term.value
                    continue

                coeff, base = _extract_coefficient(term)
                coeff *= sign
                key = _signature(base)
                if key in grouped:
                    existing_coeff, existing_base = grouped[key]
                    grouped[key] = (existing_coeff + coeff, existing_base)
                else:
                    grouped[key] = (coeff, base)

            if literal_total != 0:
                ordered_terms.append(_literal(literal_total))

            for coeff, base in grouped.values():
                if coeff == 0:
                    continue
                if coeff == 1:
                    ordered_terms.append(base)
                elif coeff == -1:
                    ordered_terms.append(UnaryOperationNode(Negation(), base))
                else:
                    ordered_terms.append(BinaryOperationNode(Multiplication(), _literal(coeff), base))

            ordered_terms.sort(key=_signature)

            if not ordered_terms:
                return _literal(0)
            if len(ordered_terms) == 1:
                return ordered_terms[0]

            return _build_binary_chain(Addition(), tuple(ordered_terms))

        if isinstance(self.operation, Multiplication) and context.normalize_multiplication:
            flattened = _flatten_associative(BinaryOperationNode(self.operation, left, right), self.operation)
            coefficient = 1.0
            factors: list[ExpressionNode] = []

            for factor in flattened:
                if isinstance(factor, LiteralNode):
                    if factor.value == 0:
                        return _literal(0)
                    coefficient *= factor.value
                else:
                    factors.append(factor)

            if coefficient == 0:
                return _literal(0)

            if coefficient == -1 and factors:
                base = factors[0] if len(factors) == 1 else _build_binary_chain(self.operation, tuple(factors))
                return UnaryOperationNode(Negation(), base)

            if coefficient != 1 or not factors:
                factors.insert(0, _literal(coefficient))

            factors.sort(key=_signature)

            if len(factors) == 1:
                return factors[0]
            return _build_binary_chain(self.operation, tuple(factors))

        if isinstance(self.operation, Division) and context.normalize_multiplication:
            if isinstance(right, LiteralNode):
                if right.value == 1:
                    return left
                if right.value == -1:
                    return UnaryOperationNode(Negation(), left)
            if isinstance(left, LiteralNode) and left.value == 0:
                return _literal(0)

        if context.eliminate_identities:
            if isinstance(self.operation, Addition):
                if isinstance(left, LiteralNode) and left.value == 0:
                    return right
                if isinstance(right, LiteralNode) and right.value == 0:
                    return left
            if isinstance(self.operation, Multiplication):
                if isinstance(left, LiteralNode):
                    if left.value == 0:
                        return _literal(0)
                    if left.value == 1:
                        return right
                if isinstance(right, LiteralNode):
                    if right.value == 0:
                        return _literal(0)
                    if right.value == 1:
                        return left
            if isinstance(self.operation, Subtraction):
                if isinstance(right, LiteralNode) and right.value == 0:
                    return left
                if isinstance(left, LiteralNode) and left.value == 0:
                    return UnaryOperationNode(Negation(), right)
            if isinstance(self.operation, Division):
                if isinstance(left, LiteralNode) and left.value == 0:
                    return _literal(0)
                if isinstance(right, LiteralNode) and right.value == 1:
                    return left

        return BinaryOperationNode(self.operation, left, right)

    def evaluate(self, namespace: Namespace) -> float:
        return self.operation.calculate(self.left.evaluate(namespace), self.right.evaluate(namespace))

    def to_expression(self) -> str:
        return f"({self.left.to_expression()}{self.operation.name}{self.right.to_expression()})"

    def signature(self) -> str:
        child_signatures = [self.left.signature(), self.right.signature()]
        if self.operation.commutative:
            child_signatures.sort()
        return f"B:{self.operation.name}({','.join(child_signatures)})"

    def __str__(self) -> str:
        return f"Binary({self.operation.name})"
