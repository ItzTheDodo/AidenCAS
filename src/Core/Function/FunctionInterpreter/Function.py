from __future__ import annotations

from typing import Optional

from Core.Function.FunctionInterpreter.FunctionAST import FunctionAST
from Core.Namespace.Namespace import Namespace
from Core.Set.Interval import Interval
from Core.Set.IntervalSet import IntervalSet


class Function:
    """Compile and evaluate a named mathematical mapping."""

    def __init__(self, raw_function: str, namespace: Optional[Namespace] = None):
        """Parse a function definition and compile its expression tree."""

        self._raw_function = raw_function
        self._namespace = namespace if namespace is not None else Namespace("local")

        print(f"Parsing function: {raw_function}")

        if namespace is not None:
            print(f"Using namespace: {namespace.name}")

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

        # Populate missing domain/codomain sets with a broad default interval.
        if self._domain not in self._namespace.sets.keys():
            self.namespace.add_set(self._domain, IntervalSet(Interval(float("-inf"), float("inf"), True, True)))
        if self._codomain not in self._namespace.sets.keys():
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
        print(f"Parsed function AST: \n{self._function_ast}")

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
        return [cls(function, namespace) for function in raw_function.splitlines() if function.strip() and not function.strip().startswith("#")]

    def __str__(self) -> str:
        """Render the original mapping expression."""
        return self.function_ast.get_raw_expression()

    def __repr__(self) -> str:
        return f"Function(name={self._name}, domain={self._domain}, codomain={self._codomain})"

    def evaluate(self, *n: float) -> float:
        """Evaluate the function against positional argument values."""
        if len(n) != self.get_amount_of_arguments():
            raise ValueError(f"Expected {self.get_amount_of_arguments()} arguments, got {len(n)}")
        local_namespace = Namespace(f"{self.name}_evaluation")
        for var, value in zip(self._argument_variables, n):
            local_namespace.add_variable(var, value)
        return self._function_ast.evaluate(local_namespace)

    def simplify(self) -> Function:
        """Return a new Function with a simplified AST."""
        simplified_ast = self._function_ast.simplify_ast()
        simplified_mapping = f"{', '.join(self._argument_variables)} -> {simplified_ast.get_raw_expression()}"
        simplified_function_definition = f"{self._name}: {self._domain} -> {self._codomain}; {simplified_mapping}"
        return Function(simplified_function_definition, self.namespace)

    def get_raw_expression(self) -> str:
        """Return the raw mapping expression."""
        return self._function_ast.get_raw_expression()


if __name__ == "__main__":
    functions = Function.from_file("example_function")
    print(functions)
    f = functions[-1]
    print(f.name)
    print(f.domain)
    print(f.codomain)
    print(f.argument_variables)
    print(f.evaluate(0.1))
    print(f.function_ast.get_raw_expression())
    print("--------------------------------")
    print(f.function_ast.simplify_ast().get_raw_expression())
    print(f.simplify().get_raw_expression())
