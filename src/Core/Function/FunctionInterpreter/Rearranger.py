from __future__ import annotations

from dataclasses import dataclass

from Core.Function.BinaryOperations.Addition import Addition
from Core.Function.BinaryOperations.Division import Division
from Core.Function.BinaryOperations.Multiplication import Multiplication
from Core.Function.BinaryOperations.Negation import Negation
from Core.Function.BinaryOperations.Power import Power
from Core.Function.BinaryOperations.Subtraction import Subtraction
from Core.Function.FunctionInterpreter.ASTNodes import (
    BinaryOperationNode,
    ProductNode,
    ExpressionNode,
    FunctionCallNode,
    IdentifierNode,
    LiteralNode,
    _extract_coefficient,
    _literal,
    SimplificationContext,
    SummationNode,
    UnaryOperationNode,
)
from Core.Function.FunctionInterpreter.FunctionAST import FunctionAST


def _simplify_node(node: ExpressionNode) -> ExpressionNode:
    return FunctionAST(node).canonical_simplify_ast().root


@dataclass(frozen=True)
class _Polynomial:
    coefficients: dict[int, ExpressionNode]

    @classmethod
    def zero(cls) -> _Polynomial:
        return cls({})

    @classmethod
    def constant(cls, node: ExpressionNode) -> _Polynomial:
        if isinstance(node, LiteralNode) and node.value == 0:
            return cls.zero()
        return cls({0: _simplify_node(node)})

    @classmethod
    def variable(cls) -> _Polynomial:
        return cls({1: LiteralNode(1)})

    def normalize(self) -> _Polynomial:
        cleaned: dict[int, ExpressionNode] = {}
        for exponent, coefficient in self.coefficients.items():
            coefficient = _simplify_node(coefficient)
            if isinstance(coefficient, LiteralNode) and coefficient.value == 0:
                continue
            cleaned[exponent] = coefficient
        return _Polynomial(cleaned)

    def degree(self) -> int:
        if not self.coefficients:
            return -1
        return max(self.coefficients.keys())

    def coefficient(self, exponent: int) -> ExpressionNode:
        return self.coefficients.get(exponent, LiteralNode(0))

    def add(self, other: _Polynomial, subtract: bool = False) -> _Polynomial:
        result = dict(self.coefficients)
        for exponent, coefficient in other.coefficients.items():
            rhs = UnaryOperationNode(Negation(), coefficient) if subtract else coefficient
            if exponent in result:
                result[exponent] = _simplify_node(BinaryOperationNode(Addition(), result[exponent], rhs))
            else:
                result[exponent] = _simplify_node(rhs)
        return _Polynomial(result).normalize()

    def negate(self) -> _Polynomial:
        return _Polynomial({exp: _simplify_node(UnaryOperationNode(Negation(), coeff)) for exp, coeff in self.coefficients.items()}).normalize()

    def mul(self, other: _Polynomial) -> _Polynomial:
        if not self.coefficients or not other.coefficients:
            return _Polynomial.zero()
        result: dict[int, ExpressionNode] = {}
        for left_exp, left_coeff in self.coefficients.items():
            for right_exp, right_coeff in other.coefficients.items():
                exponent = left_exp + right_exp
                term = _simplify_node(BinaryOperationNode(Multiplication(), left_coeff, right_coeff))
                if exponent in result:
                    result[exponent] = _simplify_node(BinaryOperationNode(Addition(), result[exponent], term))
                else:
                    result[exponent] = term
        return _Polynomial(result).normalize()

    def pow(self, exponent: int) -> _Polynomial:
        if exponent < 0:
            raise NotImplementedError("Negative polynomial exponents are not supported")
        if exponent == 0:
            return _Polynomial.constant(LiteralNode(1))
        result = _Polynomial.constant(LiteralNode(1))
        base = self
        power = exponent
        while power > 0:
            if power % 2 == 1:
                result = result.mul(base)
            base = base.mul(base)
            power //= 2
        return result.normalize()

    def to_expression(self, variable: str) -> ExpressionNode:
        if not self.coefficients:
            return LiteralNode(0)

        terms: list[ExpressionNode] = []
        for exponent in sorted(self.coefficients.keys(), reverse=True):
            coefficient = self.coefficients[exponent]
            if exponent == 0:
                term = coefficient
            elif exponent == 1:
                term = coefficient if not (isinstance(coefficient, LiteralNode) and coefficient.value == 1) else IdentifierNode(variable)
                if term is coefficient:
                    term = BinaryOperationNode(Multiplication(), coefficient, IdentifierNode(variable))
            else:
                power = BinaryOperationNode(Power(), IdentifierNode(variable), LiteralNode(exponent))
                term = power if isinstance(coefficient, LiteralNode) and coefficient.value == 1 else BinaryOperationNode(Multiplication(), coefficient, power)
            terms.append(term)

        if not terms:
            return LiteralNode(0)
        expression = terms[0]
        for term in terms[1:]:
            expression = BinaryOperationNode(Addition(), expression, term)
        return _simplify_node(expression)


@dataclass(frozen=True)
class _RationalPolynomial:
    numerator: _Polynomial
    denominator: _Polynomial

    @classmethod
    def from_polynomial(cls, polynomial: _Polynomial) -> _RationalPolynomial:
        return cls(polynomial.normalize(), _Polynomial.constant(LiteralNode(1)))

    def pow(self, exponent: int) -> _RationalPolynomial:
        if exponent == 0:
            return _RationalPolynomial.from_polynomial(_Polynomial.constant(LiteralNode(1)))
        if exponent < 0:
            positive = self.pow(-exponent)
            return _RationalPolynomial(positive.denominator, positive.numerator)
        return _RationalPolynomial(self.numerator.pow(exponent).normalize(), self.denominator.pow(exponent).normalize())

    def add(self, other: _RationalPolynomial, subtract: bool = False) -> _RationalPolynomial:
        left = self.numerator.mul(other.denominator)
        right = other.numerator.mul(self.denominator)
        numerator = left.add(right, subtract=subtract)
        denominator = self.denominator.mul(other.denominator)
        return _RationalPolynomial(numerator.normalize(), denominator.normalize())

    def mul(self, other: _RationalPolynomial) -> _RationalPolynomial:
        return _RationalPolynomial(self.numerator.mul(other.numerator).normalize(), self.denominator.mul(other.denominator).normalize())

    def div(self, other: _RationalPolynomial) -> _RationalPolynomial:
        return _RationalPolynomial(self.numerator.mul(other.denominator).normalize(), self.denominator.mul(other.numerator).normalize())


class Rearranger:
    """Symbolically isolate a variable in a single-argument function."""

    def __init__(self, source_function, variable: str, value_name: str = "y"):
        self._source = source_function
        self._variable = variable
        self._value_name = value_name
        self._target_value = IdentifierNode(value_name)

    def rearrange(self) -> ExpressionNode:
        source = self._inline_function_calls(self._source.function_ast.canonical_simplify_ast().root)
        try:
            rearranged = self._solve_exponential_term(source, self._variable, self._target_value)
            return FunctionAST(rearranged).simplify_ast(SimplificationContext(normalize_addition=False)).root
        except (NotImplementedError, ValueError):
            pass
        try:
            rearranged = self._solve_single_root_term(source, self._variable, self._target_value)
            return FunctionAST(rearranged).simplify_ast(SimplificationContext(normalize_addition=False)).root
        except (NotImplementedError, ValueError):
            pass
        try:
            rearranged = self._solve_lambertw_term(source, self._variable, self._target_value)
            return FunctionAST(rearranged).simplify_ast(SimplificationContext(normalize_addition=False)).root
        except (NotImplementedError, ValueError):
            pass
        try:
            rearranged = self._rearrange_expression(source, self._variable, self._target_value)
        except (NotImplementedError, ValueError):
            rearranged = self._solve_rational_polynomial(source, self._variable, self._target_value)
        return FunctionAST(rearranged).simplify_ast(SimplificationContext(normalize_addition=False)).root

    def _rearrange_aggregate(self, node: ExpressionNode, variable: str, target_value: ExpressionNode) -> ExpressionNode | None:
        if not isinstance(node, (SummationNode, ProductNode)):
            return None
        if node.bound_variable == variable:
            return None
        if self._contains_identifier(node.lower, variable) or self._contains_identifier(node.upper, variable):
            return None
        if not self._contains_identifier(node.body, variable):
            return None

        rearranged_body = self._rearrange_expression(node.body, variable, target_value)
        if isinstance(node, SummationNode):
            return SummationNode(node.bound_variable, node.lower, node.upper, rearranged_body)
        return ProductNode(node.bound_variable, node.lower, node.upper, rearranged_body)

    def _collect_identifiers(self, node: ExpressionNode) -> set[str]:
        identifiers: set[str] = set()
        if isinstance(node, IdentifierNode):
            identifiers.add(node.name)
        for child in node.children:
            identifiers.update(self._collect_identifiers(child))
        return identifiers

    def _contains_identifier(self, node: ExpressionNode, name: str) -> bool:
        return name in self._collect_identifiers(node)

    def _is_numeric_literal(self, node: ExpressionNode) -> bool:
        return isinstance(node, LiteralNode)

    def _is_constant_term(self, node: ExpressionNode, variable: str) -> bool:
        return not self._contains_identifier(node, variable)

    def _linear_decompose(self, node: ExpressionNode, variable: str) -> tuple[ExpressionNode, ExpressionNode] | None:
        if isinstance(node, IdentifierNode) and node.name == variable:
            return LiteralNode(1), LiteralNode(0)

        if self._is_constant_term(node, variable):
            return LiteralNode(0), node

        if isinstance(node, UnaryOperationNode) and isinstance(node.operation, Negation):
            inner = self._linear_decompose(node.child, variable)
            if inner is None:
                return None
            coeff, offset = inner
            return UnaryOperationNode(Negation(), coeff), UnaryOperationNode(Negation(), offset)

        if isinstance(node, BinaryOperationNode):
            if isinstance(node.operation, Addition):
                left = self._linear_decompose(node.left, variable)
                right = self._linear_decompose(node.right, variable)
                if left is not None and right is not None:
                    return BinaryOperationNode(Addition(), left[0], right[0]), BinaryOperationNode(Addition(), left[1], right[1])
            if isinstance(node.operation, Subtraction):
                left = self._linear_decompose(node.left, variable)
                right = self._linear_decompose(node.right, variable)
                if left is not None and right is not None:
                    return BinaryOperationNode(Subtraction(), left[0], right[0]), BinaryOperationNode(Subtraction(), left[1], right[1])
            if isinstance(node.operation, Multiplication):
                left_const = self._is_constant_term(node.left, variable)
                right_const = self._is_constant_term(node.right, variable)
                if left_const:
                    right = self._linear_decompose(node.right, variable)
                    if right is not None:
                        return (
                            BinaryOperationNode(Multiplication(), node.left, right[0]),
                            BinaryOperationNode(Multiplication(), node.left, right[1]),
                        )
                if right_const:
                    left = self._linear_decompose(node.left, variable)
                    if left is not None:
                        return (
                            BinaryOperationNode(Multiplication(), left[0], node.right),
                            BinaryOperationNode(Multiplication(), left[1], node.right),
                        )
            if isinstance(node.operation, Division) and self._is_constant_term(node.right, variable):
                left = self._linear_decompose(node.left, variable)
                if left is not None:
                    return (
                        BinaryOperationNode(Division(), left[0], node.right),
                        BinaryOperationNode(Division(), left[1], node.right),
                    )

        return None

    def _is_power_term(self, node: ExpressionNode, variable: str) -> bool:
        if not isinstance(node, BinaryOperationNode) or not isinstance(node.operation, Power):
            return False
        if not self._contains_identifier(node.left, variable):
            return False
        return self._is_numeric_literal(node.right)

    def _contains_power_term(self, node: ExpressionNode, variable: str) -> bool:
        if self._is_power_term(node, variable):
            return True
        return any(self._contains_power_term(child, variable) for child in node.children)

    def _is_root_term(self, node: ExpressionNode, variable: str) -> bool:
        return self._is_power_term(node, variable) and isinstance(node.right, LiteralNode) and float(node.right.value) == 0.5

    def _flatten_additive_terms(self, node: ExpressionNode, sign: int = 1) -> list[tuple[int, ExpressionNode]]:
        if isinstance(node, UnaryOperationNode) and isinstance(node.operation, Negation):
            return self._flatten_additive_terms(node.child, -sign)
        if isinstance(node, BinaryOperationNode) and isinstance(node.operation, Addition):
            return self._flatten_additive_terms(node.left, sign) + self._flatten_additive_terms(node.right, sign)
        if isinstance(node, BinaryOperationNode) and isinstance(node.operation, Subtraction):
            return self._flatten_additive_terms(node.left, sign) + self._flatten_additive_terms(node.right, -sign)
        return [(sign, node)]

    def _rebuild_sum(self, terms: list[tuple[int, ExpressionNode]]) -> ExpressionNode:
        if not terms:
            return LiteralNode(0)
        expression: ExpressionNode | None = None
        for sign, term in terms:
            signed_term = term if sign > 0 else UnaryOperationNode(Negation(), term)
            expression = signed_term if expression is None else BinaryOperationNode(Addition(), expression, signed_term)
        return expression if expression is not None else LiteralNode(0)

    def _strip_scale(self, node: ExpressionNode, variable: str, target_value: ExpressionNode) -> tuple[ExpressionNode, ExpressionNode]:
        if isinstance(node, BinaryOperationNode) and isinstance(node.operation, Multiplication):
            left_has = self._contains_identifier(node.left, variable)
            right_has = self._contains_identifier(node.right, variable)
            if left_has and not right_has:
                return node.left, BinaryOperationNode(Division(), target_value, node.right)
            if right_has and not left_has:
                return node.right, BinaryOperationNode(Division(), target_value, node.left)
        if isinstance(node, BinaryOperationNode) and isinstance(node.operation, Division):
            left_has = self._contains_identifier(node.left, variable)
            right_has = self._contains_identifier(node.right, variable)
            if left_has and not right_has:
                return node.left, BinaryOperationNode(Multiplication(), target_value, node.right)
        return node, target_value

    def _solve_single_root_term(self, node: ExpressionNode, variable: str, target_value: ExpressionNode) -> ExpressionNode:
        node, target_value = self._strip_scale(node, variable, target_value)
        terms = self._flatten_additive_terms(node)
        root_terms = [(sign, term) for sign, term in terms if self._is_root_term(term, variable)]
        if len(root_terms) != 1:
            raise NotImplementedError("Root-term solver requires exactly one square-root term")

        sign, root_term = root_terms[0]
        other_expr = self._rebuild_sum([(term_sign, term) for term_sign, term in terms if term is not root_term])
        isolated_root = BinaryOperationNode(Subtraction(), target_value, other_expr) if sign > 0 else BinaryOperationNode(Subtraction(), other_expr, target_value)
        squared_target = BinaryOperationNode(Power(), isolated_root, LiteralNode(2))
        return self._solve_rational_polynomial(root_term.left, variable, squared_target)

    def _solve_exponential_term(self, node: ExpressionNode, variable: str, target_value: ExpressionNode) -> ExpressionNode:
        exp_function = self._source.namespace.functions.get("exp")
        log_function = self._source.namespace.functions.get("log")
        lambertw_function = self._source.namespace.functions.get("lambertw")
        if exp_function is None or log_function is None or lambertw_function is None:
            raise ValueError("Exponential solving requires builtin exp(), log(), and lambertw()")

        if isinstance(node, BinaryOperationNode) and isinstance(node.operation, Power):
            left_has = self._contains_identifier(node.left, variable)
            right_has = self._contains_identifier(node.right, variable)

            if left_has and not right_has:
                exponent = self._linear_decompose(node.right, variable)
                if exponent is None:
                    raise NotImplementedError("Power solver needs a constant exponent")
                coeff, offset = exponent
                if isinstance(coeff, LiteralNode) and coeff.value == 0:
                    return BinaryOperationNode(Power(), target_value, BinaryOperationNode(Division(), LiteralNode(1), offset))
                raise NotImplementedError("Power solver only supports constant exponents when the variable is in the base")

            if right_has and not left_has:
                exponent = self._linear_decompose(node.right, variable)
                if exponent is None:
                    raise NotImplementedError("Power solver needs a constant or affine exponent")
                coeff, offset = exponent
                if isinstance(node.left, IdentifierNode) and node.left.name == variable and isinstance(coeff, LiteralNode) and coeff.value == 1 and isinstance(offset, LiteralNode) and offset.value == 0:
                    log_target = FunctionCallNode(log_function, (target_value,))
                    return FunctionCallNode(exp_function, (FunctionCallNode(lambertw_function, (log_target,)),))

                if self._is_constant_term(node.left, variable):
                    log_base = FunctionCallNode(log_function, (node.left,))
                    numerator = BinaryOperationNode(Subtraction(), BinaryOperationNode(Division(), FunctionCallNode(log_function, (target_value,)), log_base), offset)
                    return BinaryOperationNode(Division(), numerator, coeff)

            if left_has and right_has and node.left.signature() == node.right.signature():
                log_target = FunctionCallNode(log_function, (target_value,))
                return FunctionCallNode(exp_function, (FunctionCallNode(lambertw_function, (log_target,)),))

        if isinstance(node, BinaryOperationNode) and isinstance(node.operation, Multiplication):
            left_constant = self._is_constant_term(node.left, variable)
            right_constant = self._is_constant_term(node.right, variable)
            if left_constant and not right_constant:
                return self._solve_exponential_term(node.right, variable, BinaryOperationNode(Division(), target_value, node.left))
            if right_constant and not left_constant:
                return self._solve_exponential_term(node.left, variable, BinaryOperationNode(Division(), target_value, node.right))

            def solve_product(variable_factor: ExpressionNode, other_factor: ExpressionNode) -> ExpressionNode | None:
                factor_coeff, factor_base = _extract_coefficient(variable_factor)
                if not (isinstance(factor_base, IdentifierNode) and factor_base.name == variable):
                    return None
                factor_coeff_node = _literal(factor_coeff)

                if isinstance(other_factor, FunctionCallNode) and other_factor.function.name == "exp" and len(other_factor.arguments) == 1:
                    affine = self._linear_decompose(other_factor.arguments[0], variable)
                    if affine is None:
                        return None
                    scale, offset = affine
                    if self._is_constant_term(scale, variable) and self._is_constant_term(offset, variable):
                        multiplier = BinaryOperationNode(Multiplication(), factor_coeff_node, FunctionCallNode(exp_function, (offset,)))
                        inner = BinaryOperationNode(Division(), BinaryOperationNode(Multiplication(), scale, target_value), multiplier)
                        return BinaryOperationNode(Division(), FunctionCallNode(lambertw_function, (inner,)), scale)

                if isinstance(other_factor, BinaryOperationNode) and isinstance(other_factor.operation, Power) and self._is_constant_term(other_factor.left, variable):
                    affine = self._linear_decompose(other_factor.right, variable)
                    if affine is None:
                        return None
                    scale, offset = affine
                    if self._is_constant_term(scale, variable) and self._is_constant_term(offset, variable):
                        log_base = FunctionCallNode(log_function, (other_factor.left,))
                        multiplier = BinaryOperationNode(Multiplication(), factor_coeff_node, BinaryOperationNode(Power(), other_factor.left, offset))
                        inner = BinaryOperationNode(Division(), BinaryOperationNode(Multiplication(), BinaryOperationNode(Multiplication(), scale, log_base), target_value), multiplier)
                        return BinaryOperationNode(Division(), FunctionCallNode(lambertw_function, (inner,)), BinaryOperationNode(Multiplication(), scale, log_base))

                return None

            result = solve_product(node.left, node.right)
            if result is not None:
                return result
            result = solve_product(node.right, node.left)
            if result is not None:
                return result

        raise NotImplementedError("No dedicated exponential solution matched")

    def _solve_lambertw_term(self, node: ExpressionNode, variable: str, target_value: ExpressionNode) -> ExpressionNode:
        if not isinstance(node, BinaryOperationNode) or not isinstance(node.operation, Multiplication):
            raise NotImplementedError("Lambert W solver requires a simple product")

        lambertw_function = self._source.namespace.functions.get("lambertw")
        if lambertw_function is None:
            raise ValueError("Lambert W solver requires builtin exp() and lambertw()")

        def is_exp_of_variable(term: ExpressionNode) -> bool:
            return isinstance(term, FunctionCallNode) and term.function.name == "exp" and len(term.arguments) == 1 and self._contains_identifier(term.arguments[0], variable)

        if is_exp_of_variable(node.left) and self._contains_identifier(node.right, variable):
            return FunctionCallNode(lambertw_function, (target_value,))
        if is_exp_of_variable(node.right) and self._contains_identifier(node.left, variable):
            return FunctionCallNode(lambertw_function, (target_value,))

        raise NotImplementedError("Lambert W solver only supports x*exp(x)-style products")

    def _invert_numeric_power(self, target_value: ExpressionNode, exponent: ExpressionNode) -> ExpressionNode:
        return BinaryOperationNode(Power(), target_value, BinaryOperationNode(Division(), LiteralNode(1), exponent))

    def _inline_function_calls(self, node: ExpressionNode, seen: set[str] | None = None) -> ExpressionNode:
        seen = set() if seen is None else set(seen)
        if isinstance(node, IdentifierNode) or isinstance(node, LiteralNode):
            return node
        if isinstance(node, UnaryOperationNode):
            return UnaryOperationNode(node.operation, self._inline_function_calls(node.child, seen))
        if isinstance(node, BinaryOperationNode):
            return BinaryOperationNode(
                node.operation,
                self._inline_function_calls(node.left, seen),
                self._inline_function_calls(node.right, seen),
            )
        if isinstance(node, FunctionCallNode):
            arguments = tuple(self._inline_function_calls(argument, seen) for argument in node.arguments)
            if node.function.name in {"exp", "log"} or node.function.name in seen:
                return FunctionCallNode(node.function, arguments)
            mapping = {name: argument for name, argument in zip(node.function.argument_variables, arguments)}
            inlined = node.function.function_ast.substitute(mapping).canonical_simplify_ast().root
            return self._inline_function_calls(inlined, seen | {node.function.name})
        return node

    def _to_rational_polynomial(self, node: ExpressionNode, variable: str) -> _RationalPolynomial:
        node = self._inline_function_calls(node)
        if isinstance(node, LiteralNode):
            return _RationalPolynomial.from_polynomial(_Polynomial.constant(node))
        if isinstance(node, IdentifierNode):
            if node.name == variable:
                return _RationalPolynomial.from_polynomial(_Polynomial.variable())
            return _RationalPolynomial.from_polynomial(_Polynomial.constant(node))
        if isinstance(node, UnaryOperationNode):
            rational = self._to_rational_polynomial(node.child, variable)
            return _RationalPolynomial(rational.numerator.negate(), rational.denominator)
        if isinstance(node, BinaryOperationNode):
            left = self._to_rational_polynomial(node.left, variable)
            right = self._to_rational_polynomial(node.right, variable)
            if isinstance(node.operation, Addition):
                return left.add(right)
            if isinstance(node.operation, Subtraction):
                return left.add(right, subtract=True)
            if isinstance(node.operation, Multiplication):
                return left.mul(right)
            if isinstance(node.operation, Division):
                return left.div(right)
            if isinstance(node.operation, Power):
                if not isinstance(node.right, LiteralNode) or not float(node.right.value).is_integer():
                    raise NotImplementedError("Polynomial solver only supports integer power exponents")
                return left.pow(int(node.right.value))
        raise NotImplementedError(f"Polynomial solver does not support node type '{type(node).__name__}'")

    def _solve_rational_polynomial(self, node: ExpressionNode, variable: str, target_value: ExpressionNode) -> ExpressionNode:
        equation = BinaryOperationNode(Subtraction(), node, target_value)
        rational = self._to_rational_polynomial(equation, variable)
        numerator = rational.numerator.normalize()
        degree = numerator.degree()

        if degree < 1:
            raise NotImplementedError("Equation does not contain the target variable in polynomial form")

        if degree == 1:
            a = numerator.coefficient(1)
            b = numerator.coefficient(0)
            return _simplify_node(BinaryOperationNode(Division(), UnaryOperationNode(Negation(), b), a))

        if degree == 2:
            a = numerator.coefficient(2)
            b = numerator.coefficient(1)
            c = numerator.coefficient(0)
            four_ac = BinaryOperationNode(Multiplication(), LiteralNode(4), BinaryOperationNode(Multiplication(), a, c))
            discriminant = BinaryOperationNode(Subtraction(), BinaryOperationNode(Power(), b, LiteralNode(2)), four_ac)
            sqrt_discriminant = BinaryOperationNode(Power(), discriminant, LiteralNode(0.5))
            neg_b = UnaryOperationNode(Negation(), b)
            numerator_expr = BinaryOperationNode(Addition(), neg_b, sqrt_discriminant)
            denominator_expr = BinaryOperationNode(Multiplication(), LiteralNode(2), a)
            return _simplify_node(BinaryOperationNode(Division(), numerator_expr, denominator_expr))

        raise NotImplementedError("Polynomial solver currently supports only linear and quadratic equations")

    def _rearrange_expression(self, node: ExpressionNode, variable: str, target_value: ExpressionNode) -> ExpressionNode:
        if isinstance(node, IdentifierNode):
            if node.name != variable:
                raise NotImplementedError(f"Cannot rearrange through identifier '{node.name}'")
            return target_value

        if isinstance(node, UnaryOperationNode) and isinstance(node.operation, Negation):
            if self._contains_identifier(node.child, variable):
                return self._rearrange_expression(node.child, variable, UnaryOperationNode(Negation(), target_value))

        if isinstance(node, FunctionCallNode):
            containing_arguments = [index for index, argument in enumerate(node.arguments) if self._contains_identifier(argument, variable)]

            if not containing_arguments:
                raise ValueError(f"Variable '{variable}' not found in expression")

            if len(containing_arguments) > 1:
                raise NotImplementedError("Rearrange only supports one variable-containing argument per function call")

            argument = node.arguments[containing_arguments[0]]

            substitutions = {
                name: value
                for name, value in zip(node.function.argument_variables, node.arguments)
                if not self._contains_identifier(value, variable)
            }

            specialized_function = node.function.substitute(substitutions) if substitutions else node.function
            inverse_function = specialized_function.inverse()
            inverse_value = inverse_function.function_ast.substitute({inverse_function.argument_variables[0]: target_value}).root
            return self._rearrange_expression(argument, variable, inverse_value)

        aggregate_result = self._rearrange_aggregate(node, variable, target_value)
        if aggregate_result is not None:
            return aggregate_result

        if not isinstance(node, BinaryOperationNode):
            raise NotImplementedError(f"Cannot rearrange through node type '{type(node).__name__}'")

        left_has = self._contains_identifier(node.left, variable)
        right_has = self._contains_identifier(node.right, variable)

        if left_has and right_has:
            if isinstance(node.operation, Addition):
                if self._is_power_term(node.left, variable):
                    next_target = BinaryOperationNode(Subtraction(), target_value, node.right)
                    inverted_target = self._invert_numeric_power(next_target, node.left.right)
                    try:
                        return self._solve_rational_polynomial(node.left.left, variable, inverted_target)
                    except (NotImplementedError, ValueError):
                        return self._rearrange_expression(node.left, variable, next_target)
                if self._is_power_term(node.right, variable):
                    next_target = BinaryOperationNode(Subtraction(), target_value, node.left)
                    inverted_target = self._invert_numeric_power(next_target, node.right.right)
                    try:
                        return self._solve_rational_polynomial(node.right.left, variable, inverted_target)
                    except (NotImplementedError, ValueError):
                        return self._rearrange_expression(node.right, variable, next_target)

            if isinstance(node.operation, Subtraction):
                if self._is_power_term(node.left, variable):
                    next_target = BinaryOperationNode(Addition(), target_value, node.right)
                    inverted_target = self._invert_numeric_power(next_target, node.left.right)
                    try:
                        return self._solve_rational_polynomial(node.left.left, variable, inverted_target)
                    except (NotImplementedError, ValueError):
                        return self._rearrange_expression(node.left, variable, next_target)
                if self._is_power_term(node.right, variable):
                    next_target = BinaryOperationNode(Subtraction(), node.left, target_value)
                    inverted_target = self._invert_numeric_power(next_target, node.right.right)
                    try:
                        return self._solve_rational_polynomial(node.right.left, variable, inverted_target)
                    except (NotImplementedError, ValueError):
                        return self._rearrange_expression(node.right, variable, next_target)

            raise NotImplementedError("Rearrange only supports a single occurrence of the target variable per expression branch")
        if not left_has and not right_has:
            raise ValueError(f"Variable '{variable}' not found in expression")

        if isinstance(node.operation, Addition):
            next_target = BinaryOperationNode(Subtraction(), target_value, node.right if left_has else node.left)
            return self._rearrange_expression(node.left if left_has else node.right, variable, next_target)

        if isinstance(node.operation, Subtraction):
            if left_has:
                next_target = BinaryOperationNode(Addition(), target_value, node.right)
                return self._rearrange_expression(node.left, variable, next_target)
            next_target = BinaryOperationNode(Subtraction(), node.left, target_value)
            return self._rearrange_expression(node.right, variable, next_target)

        if isinstance(node.operation, Multiplication):
            exp_function = self._source.namespace.functions.get("exp")
            lambertw_function = self._source.namespace.functions.get("lambertw")
            if exp_function is not None and lambertw_function is not None:
                if isinstance(node.left, FunctionCallNode) and node.left.function.name == "exp" and len(node.left.arguments) == 1 and self._contains_identifier(node.left.arguments[0], variable) and self._contains_identifier(node.right, variable) and self._collect_identifiers(node.left.arguments[0]) == self._collect_identifiers(node.right):
                    return FunctionCallNode(lambertw_function, (target_value,))
                if isinstance(node.right, FunctionCallNode) and node.right.function.name == "exp" and len(node.right.arguments) == 1 and self._contains_identifier(node.right.arguments[0], variable) and self._contains_identifier(node.left, variable) and self._collect_identifiers(node.right.arguments[0]) == self._collect_identifiers(node.left):
                    return FunctionCallNode(lambertw_function, (target_value,))
            next_target = BinaryOperationNode(Division(), target_value, node.right if left_has else node.left)
            return self._rearrange_expression(node.left if left_has else node.right, variable, next_target)

        if isinstance(node.operation, Division):
            if left_has:
                next_target = BinaryOperationNode(Multiplication(), target_value, node.right)
                return self._rearrange_expression(node.left, variable, next_target)
            next_target = BinaryOperationNode(Division(), node.left, target_value)
            return self._rearrange_expression(node.right, variable, next_target)

        if isinstance(node.operation, Power):
            if left_has:
                next_target = BinaryOperationNode(Power(), target_value, BinaryOperationNode(Division(), LiteralNode(1), node.right))
                return self._rearrange_expression(node.left, variable, next_target)

            if right_has:
                log_function = self._source.namespace.functions.get("log")
                if log_function is None:
                    raise ValueError("Rearranging a power exponent requires builtin log() in the namespace")
                next_target = BinaryOperationNode(
                    Division(),
                    FunctionCallNode(log_function, (target_value,)),
                    FunctionCallNode(log_function, (node.left,)),
                )
                return self._rearrange_expression(node.right, variable, next_target)

        raise NotImplementedError(f"Rearrange does not support expression node '{type(node).__name__}'")
