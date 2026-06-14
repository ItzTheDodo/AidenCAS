from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
import math
from typing import TYPE_CHECKING, Any

from Core.Function.BinaryOperations.Addition import Addition
from Core.Function.BinaryOperations.BinaryOperation import BinaryOperation
from Core.Function.BinaryOperations.Division import Division
from Core.Function.BinaryOperations.Negation import Negation
from Core.Function.BinaryOperations.Multiplication import Multiplication
from Core.Function.BinaryOperations.Power import Power
from Core.Function.BinaryOperations.Subtraction import Subtraction
from Core.Matrix.Matrix import Matrix

if TYPE_CHECKING:
    from Core.Function.FunctionInterpreter.Function import Function
    from Core.Function.FunctionInterpreter.Simplifier import SimplificationContext
    from Core.Namespace.Namespace import Namespace


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _normalize_literal_value(value: Any) -> Any:
    if isinstance(value, Matrix):
        return value
    if isinstance(value, list):
        return Matrix.from_nested(tuple(tuple(_normalize_literal_value(item) for item in row) for row in value))
    if isinstance(value, tuple):
        if value and all(isinstance(row, (list, tuple)) for row in value):
            return Matrix.from_nested(tuple(tuple(_normalize_literal_value(item) for item in row) for row in value))
        return tuple(_normalize_literal_value(item) for item in value)
    if _is_number(value):
        return float(value)
    return value


def _is_matrix_value(value: Any) -> bool:
    return isinstance(value, Matrix)


def _contains_matrix_literal(node: ExpressionNode) -> bool:
    if isinstance(node, LiteralNode) and _is_matrix_value(node.value):
        return True
    return any(_contains_matrix_literal(child) for child in node.children)


def _format_number(value: float) -> str:
    """Render numeric values without trailing `.0` when possible."""
    if float(value).is_integer():
        return str(int(value))
    text = f"{value:.17f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def _format_literal_value(value: Any) -> str:
    if _is_number(value):
        return _format_number(float(value))
    if _is_matrix_value(value):
        return value.to_expression()
    return str(value)


def _signature_literal_value(value: Any) -> str:
    if _is_number(value):
        return _format_number(float(value))
    if _is_matrix_value(value):
        return value.signature()
    return repr(value)


def _zero_like(value: Any) -> Any:
    if _is_number(value):
        return 0.0
    if _is_matrix_value(value):
        rows, cols = value.shape
        return Matrix(tuple(tuple(0.0 for _ in range(cols)) for _ in range(rows)))
    raise TypeError(f"Unsupported literal type: {type(value).__name__}")


def _negate_literal_values(value: Any) -> Any:
    if _is_number(value):
        return -float(value)
    if _is_matrix_value(value):
        return value.negate()
    raise TypeError(f"Unsupported literal type: {type(value).__name__}")


def _literal(value: Any) -> LiteralNode:
    return LiteralNode(_normalize_literal_value(value))


def _matrix_dimensions(value: Any) -> tuple[int, int] | None:
    if not _is_matrix_value(value):
        return None
    return value.shape


def _add_literal_values(left: Any, right: Any) -> Any:
    if _is_number(left) and _is_number(right):
        return float(left) + float(right)
    if _is_matrix_value(left) and _is_matrix_value(right):
        return left.add(right)
    if _is_matrix_value(left) and _is_number(right):
        return left.add(float(right))
    if _is_number(left) and _is_matrix_value(right):
        return right.add(float(left))
    raise TypeError("Unsupported literal addition")


def _subtract_literal_values(left: Any, right: Any) -> Any:
    if _is_number(left) and _is_number(right):
        return float(left) - float(right)
    if _is_matrix_value(left) and _is_matrix_value(right):
        return left.subtract(right)
    if _is_matrix_value(left) and _is_number(right):
        return left.subtract(float(right))
    if _is_number(left) and _is_matrix_value(right):
        return Matrix.from_nested(tuple(tuple(float(left) - item for item in row) for row in right.rows))
    raise TypeError("Unsupported literal subtraction")


def _multiply_matrix_values(left: Any, right: Any) -> Any:
    if _is_number(left) and _is_number(right):
        return float(left) * float(right)
    if _is_matrix_value(left) and _is_number(right):
        return left.multiply(float(right))
    if _is_number(left) and _is_matrix_value(right):
        return right.multiply(float(left))
    if _is_matrix_value(left) and _is_matrix_value(right):
        return left.multiply(right)
    raise TypeError("Unsupported literal multiplication")


def _divide_literal_values(left: Any, right: Any) -> Any:
    if _is_number(left) and _is_number(right):
        return float(left) / float(right)
    if _is_matrix_value(left) and _is_number(right):
        return left.divide(float(right))
    raise TypeError("Unsupported literal division")


def _power_literal_values(left: Any, right: Any) -> Any:
    if _is_number(left) and _is_number(right):
        return float(left) ** float(right)
    if _is_matrix_value(left) and _is_number(right):
        return left.power(float(right))
    raise TypeError("Unsupported literal power")


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

    if isinstance(node, LiteralNode) and _is_number(node.value):
        return float(node.value), _literal(1)

    if isinstance(node, BinaryOperationNode) and isinstance(node.operation, Multiplication):
        factors = _flatten_associative(node, node.operation)
        coefficient = 1.0
        remaining: list[ExpressionNode] = []
        for factor in factors:
            if isinstance(factor, LiteralNode) and _is_number(factor.value):
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
        if isinstance(denominator, LiteralNode) and _is_number(denominator.value) and denominator.value != 0:
            return 1 / denominator.value, numerator

    return 1.0, node


def _extract_power_factor(node: ExpressionNode) -> tuple[ExpressionNode, ExpressionNode] | None:
    """Return a base/exponent pair for multiplicative power-like factors."""
    if isinstance(node, IdentifierNode):
        return node, _literal(1)

    if isinstance(node, BinaryOperationNode) and isinstance(node.operation, Power):
        return node.left, node.right

    if isinstance(node, BinaryOperationNode) and isinstance(node.operation, Division):
        if isinstance(node.left, LiteralNode) and node.left.value == 1:
            if isinstance(node.right, BinaryOperationNode) and isinstance(node.right.operation, Power):
                return node.right.left, UnaryOperationNode(Negation(), node.right.right)
            return node.right, _literal(-1)

    return None


def _decompose_product(node: ExpressionNode) -> tuple[float, list[ExpressionNode]]:
    """Flatten a multiplicative expression into coefficient and factors."""
    if isinstance(node, BinaryOperationNode) and isinstance(node.operation, Multiplication):
        flattened = _flatten_associative(node, node.operation)
    else:
        flattened = (node,)

    coefficient = 1.0
    factors: list[ExpressionNode] = []
    for factor in flattened:
        if isinstance(factor, LiteralNode) and _is_number(factor.value):
            if factor.value == 0:
                return 0.0, []
            coefficient *= factor.value
            continue
        factors.append(factor)

    return coefficient, factors


def _canonicalize_factors(
    factors: list[ExpressionNode],
    context: SimplificationContext,
    *,
    coefficient: float = 1.0,
) -> ExpressionNode:
    """Return a canonical product built from a coefficient and factor list."""
    if coefficient == 0:
        return _literal(0)

    power_groups: dict[str, tuple[ExpressionNode, ExpressionNode]] = {}
    remaining_factors: list[ExpressionNode] = []

    for factor in factors:
        power_factor = _extract_power_factor(factor)
        if power_factor is None:
            remaining_factors.append(factor)
            continue

        base, exponent = power_factor
        key = base.signature()
        if key in power_groups:
            existing_base, existing_exponent = power_groups[key]
            power_groups[key] = (existing_base, _combine_exponents(existing_exponent, exponent, context))
        else:
            power_groups[key] = (base, exponent)

    normalized_factors: list[ExpressionNode] = []
    power_context = replace(context, normalize_addition=False)
    for base, exponent in power_groups.values():
        normalized_factors.append(BinaryOperationNode(Power(), base, exponent).simplify(power_context))

    normalized_factors.extend(remaining_factors)
    normalized_factors = [
        factor
        for factor in normalized_factors
        if not (isinstance(factor, LiteralNode) and factor.value == 1)
    ]

    if coefficient == -1 and normalized_factors:
        base = normalized_factors[0] if len(normalized_factors) == 1 else _build_binary_chain(Multiplication(), tuple(normalized_factors))
        return UnaryOperationNode(Negation(), base)

    if coefficient != 1 or not normalized_factors:
        normalized_factors.insert(0, _literal(coefficient))

    normalized_factors.sort(key=_signature)

    if len(normalized_factors) == 1:
        return normalized_factors[0]
    return _build_binary_chain(Multiplication(), tuple(normalized_factors))


def _combine_exponents(left: ExpressionNode, right: ExpressionNode, context: SimplificationContext) -> ExpressionNode:
    """Build a readable exponent sum while preserving algebraic meaning."""
    power_context = replace(context, normalize_addition=False)
    terms = _collect_signed_terms(BinaryOperationNode(Addition(), left, right))
    positives: list[ExpressionNode] = []
    negatives: list[ExpressionNode] = []
    for sign, term in terms:
        effective_sign = sign
        effective_term = term
        if isinstance(term, LiteralNode) and term.value < 0:
            effective_sign *= -1
            effective_term = _literal(-term.value)
        elif isinstance(term, UnaryOperationNode) and isinstance(term.operation, Negation) and isinstance(term.child, LiteralNode):
            effective_sign *= -1
            effective_term = _literal(term.child.value)

        if effective_sign < 0:
            negatives.append(effective_term)
        else:
            positives.append(effective_term)

    def build_addition(items: list[ExpressionNode]) -> ExpressionNode:
        if not items:
            return _literal(0)
        if len(items) == 1:
            return items[0]
        items = sorted(items, key=lambda item: (isinstance(item, LiteralNode), item.signature()))
        return _build_binary_chain(Addition(), tuple(items))

    result = build_addition(positives)
    if negatives:
        negative_term = build_addition(negatives)
        result = BinaryOperationNode(Subtraction(), result, negative_term)

    return result.simplify(power_context)


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


def _substitute(node: ExpressionNode, mapping: dict[str, ExpressionNode]) -> ExpressionNode:
    """Replace identifiers with expression subtrees, preserving immutability."""
    if isinstance(node, IdentifierNode) and node.name in mapping:
        return mapping[node.name]
    if isinstance(node, UnaryOperationNode):
        return UnaryOperationNode(node.operation, _substitute(node.child, mapping))
    if isinstance(node, FunctionCallNode):
        return FunctionCallNode(node.function, tuple(_substitute(arg, mapping) for arg in node.arguments))
    if isinstance(node, SummationNode):
        filtered = {name: value for name, value in mapping.items() if name != node.bound_variable}
        return SummationNode(
            node.bound_variable,
            _substitute(node.lower, filtered),
            _substitute(node.upper, filtered),
            _substitute(node.body, filtered),
        )
    if isinstance(node, ProductNode):
        filtered = {name: value for name, value in mapping.items() if name != node.bound_variable}
        return ProductNode(
            node.bound_variable,
            _substitute(node.lower, filtered),
            _substitute(node.upper, filtered),
            _substitute(node.body, filtered),
        )
    if isinstance(node, BinaryOperationNode):
        return BinaryOperationNode(node.operation, _substitute(node.left, mapping), _substitute(node.right, mapping))
    return node


def _collect_identifiers(node: ExpressionNode) -> set[str]:
    identifiers: set[str] = set()
    if isinstance(node, IdentifierNode):
        identifiers.add(node.name)
    for child in node.children:
        identifiers.update(_collect_identifiers(child))
    return identifiers


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
    def derivative(self, variable: str) -> ExpressionNode:
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
    value: Any

    @property
    def children(self) -> tuple[ExpressionNode, ...]:
        return ()

    def simplify(self, context: SimplificationContext) -> ExpressionNode:
        """Literals are already in simplest form."""
        return self

    def derivative(self, variable: str) -> ExpressionNode:
        return _literal(_zero_like(self.value))

    def evaluate(self, namespace: Namespace) -> Any:
        return self.value

    def to_expression(self) -> str:
        return _format_literal_value(self.value)

    def signature(self) -> str:
        return f"L:{_signature_literal_value(self.value)}"

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

    def derivative(self, variable: str) -> ExpressionNode:
        return _literal(1 if self.name == variable else 0)

    def evaluate(self, namespace: Namespace) -> Any:
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
            return _literal(_negate_literal_values(child.value))

        return UnaryOperationNode(self.operation, child)

    def derivative(self, variable: str) -> ExpressionNode:
        return UnaryOperationNode(self.operation, self.child.derivative(variable))

    def evaluate(self, namespace: Namespace) -> Any:
        value = self.child.evaluate(namespace)
        return _negate_literal_values(value)

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
        if hasattr(self.function, "build_node"):
            return self.function.build_node(args).simplify(context)
        if len(args) == 1 and isinstance(args[0], FunctionCallNode):
            inner_call = args[0]
            if self.function.name == "exp" and inner_call.function.name == "log":
                return inner_call.arguments[0]
            if self.function.name == "log" and inner_call.function.name == "exp":
                return inner_call.arguments[0]
        if context.fold_constants and getattr(self.function, "is_resolved", True) and args and all(isinstance(arg, LiteralNode) for arg in args):
            return _literal(self.function.evaluate(*[arg.value for arg in args]))
        return FunctionCallNode(self.function, args)

    def derivative(self, variable: str) -> ExpressionNode:
        argument_derivatives = tuple(arg.derivative(variable) for arg in self.arguments)
        if all(isinstance(item, LiteralNode) and item.value == 0 for item in argument_derivatives):
            return _literal(0)

        terms: list[ExpressionNode] = []
        substitution = {name: arg for name, arg in zip(self.function.argument_variables, self.arguments)}

        for argument_name, argument_derivative in zip(self.function.argument_variables, argument_derivatives):
            if isinstance(argument_derivative, LiteralNode) and argument_derivative.value == 0:
                continue

            partial_function = self.function.partial_derivative(argument_name)
            partial_expr = _substitute(partial_function.function_ast.root, substitution)
            terms.append(BinaryOperationNode(Multiplication(), partial_expr, argument_derivative))

        if not terms:
            return _literal(0)
        if len(terms) == 1:
            return terms[0]
        return _build_binary_chain(Addition(), tuple(terms))

    def evaluate(self, namespace: Namespace) -> Any:
        if hasattr(self.function, "build_node"):
            return self.function.build_node(self.arguments).evaluate(namespace)
        values = [arg.evaluate(namespace) for arg in self.arguments]
        if getattr(namespace, "_skip_domain_checks", False):
            return self.function._evaluate_raw(*values)
        self.function.check_domain(*values)
        return self.function.evaluate(*values)

    def to_expression(self) -> str:
        return f"{self.function.name}({','.join(arg.to_expression() for arg in self.arguments)})"

    def signature(self) -> str:
        return f"F:{self.function.name}({','.join(arg.signature() for arg in self.arguments)})"

    def __str__(self) -> str:
        return f"Call({self.function.name})"


@dataclass(frozen=True)
class AggregateNode(ExpressionNode):
    bound_variable: str
    lower: ExpressionNode
    upper: ExpressionNode
    body: ExpressionNode

    @property
    def children(self) -> tuple[ExpressionNode, ...]:
        return (self.lower, self.upper, self.body)

    def _bounds_as_ints(self, namespace: Namespace) -> tuple[int, int]:
        start_value = self.lower.evaluate(namespace)
        end_value = self.upper.evaluate(namespace)
        if not _is_number(start_value) or not _is_number(end_value):
            raise ValueError("Sigma/pi bounds must be scalar values")
        start = float(start_value)
        end = float(end_value)
        if not math.isfinite(start) or not math.isfinite(end):
            raise ValueError("Infinite bounds require a constant body")
        if not start.is_integer() or not end.is_integer():
            raise ValueError("Sigma/pi bounds must be integers")
        return int(start), int(end)


@dataclass(frozen=True)
class SummationNode(AggregateNode):
    def simplify(self, context: SimplificationContext) -> ExpressionNode:
        lower = self.lower.simplify(context)
        upper = self.upper.simplify(context)
        body = self.body.simplify(context)
        if isinstance(body, LiteralNode) and _is_number(body.value) and not _collect_identifiers(body) and (
            isinstance(lower, LiteralNode) and _is_number(lower.value) and math.isinf(lower.value)
            or isinstance(upper, LiteralNode) and _is_number(upper.value) and math.isinf(upper.value)
        ):
            if body.value == 0:
                return _literal(0)
        if isinstance(lower, LiteralNode) and isinstance(upper, LiteralNode) and _is_number(lower.value) and _is_number(upper.value) and self.bound_variable not in _collect_identifiers(body):
            start = float(lower.value)
            end = float(upper.value)
            if math.isfinite(start) and math.isfinite(end) and start.is_integer() and end.is_integer():
                start_i = int(start)
                end_i = int(end)
                count = abs(end_i - start_i) + 1
                return BinaryOperationNode(Multiplication(), _literal(count), body).simplify(context)
        if isinstance(lower, LiteralNode) and isinstance(upper, LiteralNode) and _is_number(lower.value) and _is_number(upper.value):
            start = float(lower.value)
            end = float(upper.value)
            if math.isfinite(start) and math.isfinite(end) and start.is_integer() and end.is_integer():
                start_i = int(start)
                end_i = int(end)
                step = 1 if start_i <= end_i else -1
                terms: list[ExpressionNode] = []
                for value in range(start_i, end_i + step, step):
                    terms.append(_substitute(body, {self.bound_variable: _literal(float(value))}))
                if not terms:
                    return _literal(0)
                expression = terms[0]
                for term in terms[1:]:
                    expression = BinaryOperationNode(Addition(), expression, term)
                return expression.simplify(context)
        return SummationNode(self.bound_variable, lower, upper, body)

    def derivative(self, variable: str) -> ExpressionNode:
        if variable == self.bound_variable:
            return _literal(0)
        return SummationNode(self.bound_variable, self.lower, self.upper, self.body.derivative(variable))

    def evaluate(self, namespace: Namespace) -> Any:
        if isinstance(self.lower, LiteralNode) and isinstance(self.upper, LiteralNode):
            start = float(self.lower.value)
            end = float(self.upper.value)
            if not math.isfinite(start) or not math.isfinite(end):
                if self.body.signature() == "L:0":
                    return 0.0
                raise ValueError("Infinite sigma bounds require a constant zero body")
        start_i, end_i = self._bounds_as_ints(namespace)
        total = 0.0
        step = 1 if start_i <= end_i else -1
        previous_value = namespace.variables.get(self.bound_variable)
        for value in range(start_i, end_i + step, step):
            namespace.variables[self.bound_variable] = float(value)
            total = _add_literal_values(total, self.body.evaluate(namespace))
        if previous_value is None:
            namespace.variables.pop(self.bound_variable, None)
        else:
            namespace.variables[self.bound_variable] = previous_value
        return total

    def to_expression(self) -> str:
        return f"sigma({self.bound_variable}, {self.lower.to_expression()}, {self.upper.to_expression()}, {self.body.to_expression()})"

    def signature(self) -> str:
        return f"S:{self.bound_variable}({self.lower.signature()},{self.upper.signature()},{self.body.signature()})"


@dataclass(frozen=True)
class ProductNode(AggregateNode):
    def simplify(self, context: SimplificationContext) -> ExpressionNode:
        lower = self.lower.simplify(context)
        upper = self.upper.simplify(context)
        body = self.body.simplify(context)
        if isinstance(body, LiteralNode) and not _collect_identifiers(body) and (isinstance(lower, LiteralNode) and math.isinf(lower.value) or isinstance(upper, LiteralNode) and math.isinf(upper.value)):
            if body.value == 1:
                return _literal(1)
        if isinstance(lower, LiteralNode) and isinstance(upper, LiteralNode) and _is_number(lower.value) and _is_number(upper.value) and self.bound_variable not in _collect_identifiers(body):
            start = float(lower.value)
            end = float(upper.value)
            if math.isfinite(start) and math.isfinite(end) and start.is_integer() and end.is_integer():
                start_i = int(start)
                end_i = int(end)
                count = abs(end_i - start_i) + 1
                if count == 0:
                    return _literal(1)
                result = _literal(1)
                for _ in range(count):
                    result = BinaryOperationNode(Multiplication(), result, body).simplify(context)
                return result
        if isinstance(lower, LiteralNode) and isinstance(upper, LiteralNode) and _is_number(lower.value) and _is_number(upper.value):
            start = float(lower.value)
            end = float(upper.value)
            if math.isfinite(start) and math.isfinite(end) and start.is_integer() and end.is_integer():
                start_i = int(start)
                end_i = int(end)
                step = 1 if start_i <= end_i else -1
                terms: list[ExpressionNode] = []
                for value in range(start_i, end_i + step, step):
                    terms.append(_substitute(body, {self.bound_variable: _literal(float(value))}))
                if not terms:
                    return _literal(1)
                expression = terms[0]
                for term in terms[1:]:
                    expression = BinaryOperationNode(Multiplication(), expression, term)
                return expression.simplify(context)
        return ProductNode(self.bound_variable, lower, upper, body)

    def derivative(self, variable: str) -> ExpressionNode:
        if variable == self.bound_variable:
            return _literal(0)
        product = ProductNode(self.bound_variable, self.lower, self.upper, self.body)
        quotient = BinaryOperationNode(Division(), self.body.derivative(variable), self.body)
        return BinaryOperationNode(Multiplication(), product, SummationNode(self.bound_variable, self.lower, self.upper, quotient))

    def evaluate(self, namespace: Namespace) -> Any:
        if isinstance(self.lower, LiteralNode) and isinstance(self.upper, LiteralNode):
            start = float(self.lower.value)
            end = float(self.upper.value)
            if not math.isfinite(start) or not math.isfinite(end):
                if self.body.signature() == "L:1":
                    return 1.0
                raise ValueError("Infinite product bounds require a constant one body")
        start_i, end_i = self._bounds_as_ints(namespace)
        result = 1.0
        step = 1 if start_i <= end_i else -1
        previous_value = namespace.variables.get(self.bound_variable)
        for value in range(start_i, end_i + step, step):
            namespace.variables[self.bound_variable] = float(value)
            result = _multiply_matrix_values(result, self.body.evaluate(namespace))
        if previous_value is None:
            namespace.variables.pop(self.bound_variable, None)
        else:
            namespace.variables[self.bound_variable] = previous_value
        return result

    def to_expression(self) -> str:
        return f"pi({self.bound_variable}, {self.lower.to_expression()}, {self.upper.to_expression()}, {self.body.to_expression()})"

    def signature(self) -> str:
        return f"P:{self.bound_variable}({self.lower.signature()},{self.upper.signature()},{self.body.signature()})"


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
            try:
                if isinstance(self.operation, Addition):
                    return _literal(_add_literal_values(left.value, right.value))
                if isinstance(self.operation, Subtraction):
                    return _literal(_subtract_literal_values(left.value, right.value))
                if isinstance(self.operation, Multiplication):
                    return _literal(_multiply_matrix_values(left.value, right.value))
                if isinstance(self.operation, Division):
                    return _literal(_divide_literal_values(left.value, right.value))
                if isinstance(self.operation, Power):
                    return _literal(_power_literal_values(left.value, right.value))
            except TypeError:
                pass

        if isinstance(self.operation, (Addition, Subtraction)) and context.normalize_addition:
            additive = BinaryOperationNode(self.operation, left, right)
            signed_terms = _collect_signed_terms(additive)

            literal_total = 0.0
            grouped: dict[str, tuple[float, ExpressionNode]] = {}
            ordered_terms: list[ExpressionNode] = []

            for sign, term in signed_terms:
                if isinstance(term, LiteralNode) and _is_number(term.value):
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

        if isinstance(self.operation, Multiplication) and context.normalize_multiplication and not _contains_matrix_literal(left) and not _contains_matrix_literal(right):
            coefficient, factors = _decompose_product(BinaryOperationNode(self.operation, left, right))
            return _canonicalize_factors(factors, context, coefficient=coefficient)

        if isinstance(self.operation, Division) and context.normalize_multiplication and not _contains_matrix_literal(left) and not _contains_matrix_literal(right):
            left_coefficient, left_factors = _decompose_product(left)
            right_coefficient, right_factors = _decompose_product(right)

            if left_coefficient == 0:
                return _literal(0)
            if right_coefficient == 0:
                raise ZeroDivisionError("Division by zero")

            combined_coefficient = left_coefficient / right_coefficient
            combined_factors: list[ExpressionNode] = []
            for factor in left_factors:
                power_factor = _extract_power_factor(factor)
                if power_factor is None:
                    combined_factors.append(factor)
                    continue
                base, exponent = power_factor
                combined_factors.append(BinaryOperationNode(Power(), base, exponent))

            for factor in right_factors:
                power_factor = _extract_power_factor(factor)
                if power_factor is None:
                    combined_factors.append(BinaryOperationNode(Power(), factor, _literal(-1)))
                    continue
                base, exponent = power_factor
                combined_factors.append(BinaryOperationNode(Power(), base, UnaryOperationNode(Negation(), exponent)))

            return _canonicalize_factors(combined_factors, replace(context, normalize_addition=False), coefficient=combined_coefficient)

        if isinstance(self.operation, Power):
            if isinstance(right, LiteralNode) and _is_number(right.value):
                if right.value == 1:
                    return left
                if right.value == 0:
                    return _literal(1)
            if isinstance(left, LiteralNode) and _is_number(left.value):
                if left.value == 0:
                    return _literal(0)
                if left.value == 1:
                    return _literal(1)

        if context.eliminate_identities:
            if isinstance(self.operation, Addition):
                if isinstance(left, LiteralNode) and _is_number(left.value) and left.value == 0:
                    return right
                if isinstance(right, LiteralNode) and _is_number(right.value) and right.value == 0:
                    return left
            if isinstance(self.operation, Multiplication):
                if isinstance(left, LiteralNode) and _is_number(left.value):
                    if left.value == 0:
                        return _literal(0)
                    if left.value == 1:
                        return right
                if isinstance(right, LiteralNode) and _is_number(right.value):
                    if right.value == 0:
                        return _literal(0)
                    if right.value == 1:
                        return left
            if isinstance(self.operation, Subtraction):
                if isinstance(right, LiteralNode) and _is_number(right.value) and right.value == 0:
                    return left
                if isinstance(left, LiteralNode) and _is_number(left.value) and left.value == 0:
                    return UnaryOperationNode(Negation(), right)
            if isinstance(self.operation, Division):
                if isinstance(left, LiteralNode) and _is_number(left.value) and left.value == 0:
                    return _literal(0)
                if isinstance(right, LiteralNode) and _is_number(right.value) and right.value == 1:
                    return left

        return BinaryOperationNode(self.operation, left, right)

    def derivative(self, variable: str) -> ExpressionNode:
        left_derivative = self.left.derivative(variable)
        right_derivative = self.right.derivative(variable)

        if isinstance(self.operation, Addition):
            return BinaryOperationNode(Addition(), left_derivative, right_derivative)

        if isinstance(self.operation, Subtraction):
            return BinaryOperationNode(Subtraction(), left_derivative, right_derivative)

        if isinstance(self.operation, Multiplication):
            left_term = BinaryOperationNode(Multiplication(), left_derivative, self.right)
            right_term = BinaryOperationNode(Multiplication(), self.left, right_derivative)
            return BinaryOperationNode(Addition(), left_term, right_term)

        if isinstance(self.operation, Division):
            numerator_left = BinaryOperationNode(Multiplication(), left_derivative, self.right)
            numerator_right = BinaryOperationNode(Multiplication(), self.left, right_derivative)
            numerator = BinaryOperationNode(Subtraction(), numerator_left, numerator_right)
            denominator = BinaryOperationNode(Multiplication(), self.right, self.right)
            return BinaryOperationNode(Division(), numerator, denominator)

        if isinstance(self.operation, Power):
            if isinstance(self.right, LiteralNode):
                exponent = self.right.value
                coefficient = _literal(exponent)
                new_exponent = _literal(exponent - 1)
                power_term = BinaryOperationNode(Power(), self.left, new_exponent)
                return BinaryOperationNode(
                    Multiplication(),
                    BinaryOperationNode(Multiplication(), coefficient, power_term),
                    left_derivative,
                )
            from Core.Function.Logarithm import Logarithm
            from Core.Namespace.Namespace import Namespace

            power_term = BinaryOperationNode(Power(), self.left, self.right)
            log_term = FunctionCallNode(Logarithm(Namespace("internal", load_defaults=False)), (self.left,))
            first_term = BinaryOperationNode(Multiplication(), right_derivative, log_term)
            second_term = BinaryOperationNode(
                Multiplication(),
                self.right,
                BinaryOperationNode(Division(), left_derivative, self.left),
            )
            inner = BinaryOperationNode(Addition(), first_term, second_term)
            return BinaryOperationNode(Multiplication(), power_term, inner)

        raise NotImplementedError(f"Derivative for operator '{self.operation.name}' is not implemented")

    def evaluate(self, namespace: Namespace) -> Any:
        left = self.left.evaluate(namespace)
        right = self.right.evaluate(namespace)
        if isinstance(self.operation, Addition):
            return _add_literal_values(left, right)
        if isinstance(self.operation, Subtraction):
            return _subtract_literal_values(left, right)
        if isinstance(self.operation, Multiplication):
            return _multiply_matrix_values(left, right)
        if isinstance(self.operation, Division):
            return _divide_literal_values(left, right)
        if isinstance(self.operation, Power):
            return _power_literal_values(left, right)
        return self.operation.calculate(left, right)

    def to_expression(self) -> str:
        return f"({self.left.to_expression()}{self.operation.name}{self.right.to_expression()})"

    def signature(self) -> str:
        child_signatures = [self.left.signature(), self.right.signature()]
        if self.operation.commutative:
            child_signatures.sort()
        return f"B:{self.operation.name}({','.join(child_signatures)})"

    def __str__(self) -> str:
        return f"Binary({self.operation.name})"
