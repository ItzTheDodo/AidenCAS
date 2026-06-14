from __future__ import annotations

from typing import Optional, Mapping, Any

from Core.Function.FunctionInterpreter.ASTNodes import BinaryOperationNode, ExpressionNode, IdentifierNode, LiteralNode, SimplificationContext
from Core.Function.FunctionInterpreter.ASTNodes import _normalize_literal_value
from Core.Function.FunctionInterpreter.FunctionAST import FunctionAST
from Core.Function.FunctionInterpreter.Rearranger import Rearranger
from Core.Namespace.Namespace import Namespace
from Core.Matrix.Matrix import Matrix
from Core.Function.BinaryOperations.Subtraction import Subtraction


class Function:
    """Compile and evaluate a named mathematical mapping."""

    def __init__(self, raw_function: str, namespace: Optional[Namespace] = None):
        """Parse a function definition and compile its expression tree."""

        self._raw_function = raw_function
        self._namespace = namespace if namespace is not None else Namespace("local")

        # print(f"Parsing function: {raw_function}")
        #
        # if namespace is not None:
        #     print(f"Using namespace: {namespace.name}")

        self._compile()

    def _compile(self):
        """Split the definition into name, domain, codomain, and mapping."""
        try:
            domain_definition, mapping_definition = self._raw_function.split(";", maxsplit=1)
        except ValueError:
            raise ValueError(f"Invalid function definition: {self._raw_function}. Expected format: 'name: domain -> codomain; mapping'")
        domain_definition = domain_definition.strip()
        mapping_definition = mapping_definition.strip()

        # domain parsing
        try:
            name, domain_mapping = domain_definition.split(":", maxsplit=1)
        except ValueError:
            raise ValueError(f"Invalid function definition: {self._raw_function}. Expected format: 'name: domain -> codomain; mapping'")
        self._name = name.strip()

        # Register the function early so recursive/self references can resolve.
        self.namespace.add_function(self._name, self)

        try:
            domain, codomain = domain_mapping.split("->", maxsplit=1)
        except ValueError:
            raise ValueError(f"Invalid function definition: {self._raw_function}. Expected format: 'name: domain -> codomain; mapping'")
        self._domain = domain.strip()
        self._codomain = codomain.strip()

        # Populate missing domain/codomain with broad scalar defaults.
        if self.namespace.get_domain(self._domain) is None:
            from Core.Set.Interval import Interval
            from Core.Set.IntervalSet import IntervalSet

            self.namespace.add_set(self._domain, IntervalSet(Interval(float("-inf"), float("inf"), True, True)))
        if self.namespace.get_domain(self._codomain) is None:
            from Core.Set.Interval import Interval
            from Core.Set.IntervalSet import IntervalSet

            self.namespace.add_set(self._codomain, IntervalSet(Interval(float("-inf"), float("inf"), True, True)))

        mapping_definition = mapping_definition.strip()

        try:
            actioning_variables, expression = mapping_definition.split("->", maxsplit=1)
        except ValueError:
            raise ValueError(f"Invalid mapping definition: {mapping_definition}. Expected format: 'variable -> expression'")

        self._argument_variables = [var.strip() for var in actioning_variables.split(",") if var.strip()]

        if not len(self._argument_variables) == len(set(self._argument_variables)):
            raise ValueError(f"Invalid mapping definition: {mapping_definition}. Duplicate variables found in {self._argument_variables}")

        self._function_ast = FunctionAST.from_mapping(expression.strip(), self.namespace, self._argument_variables)
        # print(f"Parsed function AST: \n{self._function_ast}")

    @property
    def namespace(self):
        return self._namespace

    @property
    def name(self) -> str:
        return self._name

    @property
    def domain(self) -> str:
        return self._domain

    @property
    def codomain(self) -> str:
        return self._codomain

    @property
    def domain_system(self):
        return self.namespace.get_domain(self._domain)

    @property
    def codomain_system(self):
        return self.namespace.get_domain(self._codomain)

    def get_amount_of_arguments(self) -> int:
        """Return the declared arity of the function."""
        return len(self._argument_variables)

    @property
    def argument_variables(self) -> list[str]:
        """Return the ordered argument names used by the expression."""
        return self._argument_variables

    @property
    def function_ast(self) -> FunctionAST:
        """Return the compiled AST for the mapping expression."""
        return self._function_ast

    @classmethod
    def from_file(cls, file_path: str, namespace: Optional[Namespace] = None) -> list[Function]:
        """Load multiple function definitions from a file, one per line."""
        namespace = namespace if namespace is not None else Namespace("local")
        with open(file_path, "r") as f:
            raw_function = f.read()
        definitions = [function for function in raw_function.splitlines() if function.strip() and not function.strip().startswith("#")]
        for definition in definitions:
            name_part = definition.split(";", maxsplit=1)[0].split(":", maxsplit=1)[0].strip()
            namespace.reserve_function(name_part)
        return [cls(function, namespace) for function in definitions]

    def __str__(self) -> str:
        """Render the original mapping expression."""
        return self.function_ast.get_raw_expression()

    def __repr__(self) -> str:
        return f"Function(name={self._name}, domain={self._domain}, codomain={self._codomain})"

    def evaluate(self, *n: Any):
        """Evaluate the function against positional argument values."""
        if len(n) != self.get_amount_of_arguments():
            raise ValueError(f"Expected {self.get_amount_of_arguments()} arguments, got {len(n)}")
        self.check_domain(*n)
        return self._evaluate_raw(*n)

    def _evaluate_raw(self, *n: Any):
        """Evaluate the function without domain validation."""
        local_namespace = Namespace(f"{self.name}_evaluation")
        setattr(local_namespace, "_skip_domain_checks", True)
        for var, value in zip(self._argument_variables, n):
            local_namespace.add_variable(var, value)
        return self._function_ast.evaluate(local_namespace)

    def _iter_scalar_values(self, value: Any):
        if isinstance(value, Matrix):
            for row in value.rows:
                for item in row:
                    yield from self._iter_scalar_values(item)
            return
        if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
            if value and any(isinstance(item, (list, tuple, Matrix)) for item in value):
                for item in value:
                    yield from self._iter_scalar_values(item)
                return
        yield value

    def _value_in_domain(self, value: Any, domain_set) -> bool:
        if hasattr(domain_set, "contains"):
            if isinstance(value, Matrix):
                try:
                    return bool(domain_set.contains(value))
                except TypeError:
                    return all(self._value_in_domain(item, domain_set) for item in self._iter_scalar_values(value))
            if isinstance(value, (int, float)):
                return bool(domain_set.contains(float(value)))
            return bool(domain_set.contains(value))
        return value in domain_set

    def check_domain(self, *values: Any) -> None:
        """Validate values against the declared domain set."""
        domain = self.domain_system
        if domain is None:
            return

        for index, value in enumerate(values):
            in_domain = domain.contains(value)

            if not in_domain:
                raise ValueError(f"Argument {index + 1}={value} is outside the domain '{self.domain}'")

    def canonical_simplify(self) -> Function:
        """Return a new Function with a canonical simplified AST."""
        simplified_ast = self._function_ast.canonical_simplify_ast()
        simplified_mapping = f"{', '.join(self._argument_variables)} -> {simplified_ast.get_raw_expression()}"
        simplified_function_definition = f"{self._name}: {self._domain} -> {self._codomain}; {simplified_mapping}"
        return Function(simplified_function_definition, self.namespace)

    def canonicalize(self) -> Function:
        """Alias for canonical_simplify()."""
        return self.canonical_simplify()

    def simplify(self) -> Function:
        """Backward-compatible alias for canonical_simplify()."""
        return self.canonical_simplify()

    def _collect_identifiers(self, node: ExpressionNode) -> set[str]:
        identifiers: set[str] = set()
        if isinstance(node, IdentifierNode):
            identifiers.add(node.name)
        for child in node.children:
            identifiers.update(self._collect_identifiers(child))
        return identifiers

    def _coerce_substitution(self, value: Any) -> ExpressionNode:
        if isinstance(value, ExpressionNode):
            return value
        if isinstance(value, FunctionAST):
            return value.root
        if isinstance(value, Function):
            return value.function_ast.root
        if isinstance(value, (int, float)):
            return LiteralNode(float(value))
        if isinstance(value, Matrix):
            return LiteralNode(value)
        if isinstance(value, (list, tuple)):
            return LiteralNode(_normalize_literal_value(value))
        if isinstance(value, str):
            return FunctionAST.from_mapping(value, self.namespace, self._argument_variables).root
        raise TypeError(f"Unsupported substitution value type: {type(value).__name__}")

    def substitute(self, substitutions: Mapping[str, Any]) -> Function:
        """Return a new Function with variables replaced by expressions or literals."""
        invalid_variables = [name for name in substitutions if name not in self._argument_variables]
        if invalid_variables:
            raise ValueError(f"Unknown substitution variable(s): {', '.join(invalid_variables)}")

        replacement_nodes = {name: self._coerce_substitution(value) for name, value in substitutions.items()}
        substituted_ast = self._function_ast.substitute(replacement_nodes).canonical_simplify_ast()
        remaining_arguments = [name for name in self._argument_variables if name not in substitutions]
        remaining_arguments = [name for name in remaining_arguments if name in self._collect_identifiers(substituted_ast.root)]

        substituted_mapping = f"{', '.join(remaining_arguments)} -> {substituted_ast.get_raw_expression()}"
        substituted_definition = f"{self._name}_sub: {self._domain} -> {self._codomain}; {substituted_mapping}"
        return Function(substituted_definition, self.namespace)

    def _derived_function(self, variable: str, suffix: str) -> Function:
        """Build a new Function from a derived AST."""
        if variable not in self._argument_variables:
            raise ValueError(f"Unknown differentiation variable: {variable}")

        cached_function = self.namespace.get_cached_derivative(self._name, variable, suffix)
        if cached_function is not None:
            return cached_function

        derived_ast = self._function_ast.derivative(variable).canonical_simplify_ast()
        derived_mapping = f"{', '.join(self._argument_variables)} -> {derived_ast.get_raw_expression()}"
        derived_name = f"{self._name}{suffix}_{variable}"
        derived_definition = f"{derived_name}: {self._domain} -> {self._codomain}; {derived_mapping}"
        return self.namespace.cache_derivative(self._name, variable, suffix, Function(derived_definition, self.namespace))

    def derivative(self, variable: str) -> Function:
        """Return the symbolic derivative as a new Function."""
        return self._derived_function(variable, "_d")

    def partial_derivative(self, variable: str) -> Function:
        """Return the symbolic partial derivative as a new Function."""
        return self.derivative(variable)

    def solve_for(
        self,
        target: float = 0.0,
        initial_guess: float = 0.0,
        max_iterations: int = 50,
        tolerance: float = 1e-8,
    ) -> float:
        """Solve a one-variable equation numerically with Newton's method."""
        if self.get_amount_of_arguments() != 1:
            raise ValueError("solve_for() only supports single-variable functions; substitute other variables first")

        variable = self._argument_variables[0]
        derivative_function = self.derivative(variable)
        estimate = float(initial_guess)

        for _ in range(max_iterations):
            value = self._evaluate_raw(estimate) - target
            if abs(value) <= tolerance:
                return estimate

            slope = derivative_function._evaluate_raw(estimate)
            if abs(slope) <= tolerance:
                raise ValueError("Cannot solve equation: derivative is too close to zero")

            next_estimate = estimate - value / slope
            if abs(next_estimate - estimate) <= tolerance:
                return next_estimate
            estimate = next_estimate

        raise ValueError("Failed to solve equation within the iteration limit")

    def solve(
        self,
        target: float = 0.0,
        initial_guess: float = 0.0,
        max_iterations: int = 50,
        tolerance: float = 1e-8,
    ) -> float:
        """Alias for solve_for() to keep the public API concise."""
        return self.solve_for(target=target, initial_guess=initial_guess, max_iterations=max_iterations, tolerance=tolerance)

    def rearrange(self, variable: str, value_name: str = "y") -> Function:
        """Symbolically isolate a chosen subject variable while preserving other parameters."""
        if variable not in self._argument_variables:
            raise ValueError(f"Unknown rearrangement variable: {variable}")

        safe_value_name = value_name
        suffix = 0
        while safe_value_name in self._argument_variables:
            suffix += 1
            safe_value_name = f"{value_name}_{suffix}"

        rearranged_node = Rearranger(self, variable, safe_value_name).rearrange()
        rearranged_ast = FunctionAST(rearranged_node).simplify_ast(SimplificationContext(normalize_addition=False))
        remaining_arguments = [name for name in self._argument_variables if name != variable]
        remaining_arguments = [name for name in remaining_arguments if name in self._collect_identifiers(rearranged_ast.root)]
        if safe_value_name not in remaining_arguments:
            remaining_arguments.append(safe_value_name)
        rearranged_definition = f"{self._name}_rearranged_{variable}: {self._codomain} -> {self._domain}; {', '.join(remaining_arguments)} -> {rearranged_ast.get_raw_expression()}"
        return Function(rearranged_definition, self.namespace)

    def rearrange_to_constant(self, variable: str, constant: Any = 0) -> Function:
        """Rearrange an equation so the result is expressed relative to a constant (default 0)."""
        if variable not in self._argument_variables:
            raise ValueError(f"Unknown rearrangement variable: {variable}")

        safe_value_name = "_rearranged"
        suffix = 0
        while safe_value_name in self._argument_variables:
            suffix += 1
            safe_value_name = f"_rearranged_{suffix}"

        rearranged_function = self.rearrange(variable, safe_value_name)
        constant_node = self._coerce_substitution(constant)
        equation_source = rearranged_function.function_ast.substitute({safe_value_name: constant_node}).root
        equation_node = BinaryOperationNode(
            Subtraction(),
            equation_source,
            IdentifierNode(variable),
        )
        equation_ast = FunctionAST(equation_node).canonical_simplify_ast()
        equation_definition = f"{self._name}_rearranged_{variable}_to_constant: {self._domain} -> {self._codomain}; {', '.join(self._argument_variables)} -> {equation_ast.get_raw_expression()}"
        return Function(equation_definition, self.namespace)

    def inverse(self, value_name: str = "y") -> Function:
        """Return the symbolic inverse of a one-variable function."""
        if self.get_amount_of_arguments() != 1:
            raise ValueError("inverse() only supports single-variable functions")
        return self.rearrange(self._argument_variables[0], value_name)

    def get_raw_expression(self) -> str:
        """Return the raw mapping expression."""
        return self._function_ast.get_raw_expression()

if __name__ == "__main__":
    functions = Function.from_file("example_function")
    # print(functions)
    # f = functions[-1]
    # print(f.name)
    # print(f.domain)
    # print(f.codomain)
    # print(f.argument_variables)
    # print(f.evaluate(0.1))
    # print(f.function_ast.get_raw_expression())
    # print("--------------------------------")
    # print(f.function_ast.simplify_ast().get_raw_expression())
    # print(f.simplify().get_raw_expression())
    func = functions[-3]
    print(func.name)
    print(func.get_raw_expression())
    print(func.simplify().get_raw_expression())
    print(func.evaluate(0.1, 0.2))
    print(func.derivative("x").simplify().get_raw_expression())

    print(functions[0].rearrange_to_constant("x", 0).get_raw_expression())

    print(functions[-1].evaluate(2))
    print(functions[-1].get_raw_expression())
    print(functions[-1].simplify().get_raw_expression())

    print(functions[1].substitute({"x":Matrix(((0.1, 0.2), (0.3, 0.4))), "y": 0.5}).get_raw_expression())

    print(func.namespace.functions)
