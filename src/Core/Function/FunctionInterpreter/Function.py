from __future__ import annotations

from typing import Optional

from Core.Function.FunctionInterpreter.FunctionAST import FunctionAST
from Core.Namespace.Namespace import Namespace
from Core.Set.Interval import Interval
from Core.Set.IntervalSet import IntervalSet


class Function:

    def __init__(self, raw_function: str, namespace: Optional[Namespace] = None):

        self._raw_function = raw_function
        self._namespace = namespace if namespace is not None else Namespace("local")

        print(f"Parsing function: {raw_function}")

        if namespace is not None:
            print(f"Using namespace: {namespace.name}")

        self._compile()

    def _compile(self):
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

        # register self function in namespace, so it can be used in its own mapping definition
        self.namespace.add_function(self._name, self)

        try:
            domain, codomain = domain_mapping.split("->", maxsplit=1)
        except ValueError:
            raise ValueError(f"Invalid function definition: {self._raw_function}. Expected format: 'name: domain -> codomain; mapping'")
        self._domain = domain.strip()
        self._codomain = codomain.strip()

        # check domain and codomain are valid, if not add them to the namespace
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

        self._function_ast = FunctionAST.from_mapping(expression.strip(), self.namespace, self._argument_variables)
        print(f"Parsed function AST: \n{self._function_ast}")
        print(FunctionAST.simplify(self._function_ast))

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
        return len(self._argument_variables)

    @property
    def argument_variables(self) -> list[str]:
        return self._argument_variables

    @property
    def function_ast(self) -> FunctionAST:
        return self._function_ast

    @classmethod
    def from_file(cls, file_path: str, namespace: Optional[Namespace] = None) -> list[Function]:
        namespace = namespace if namespace is not None else Namespace("local")
        with open(file_path, "r") as f:
            raw_function = f.read()
        return [cls(function, namespace) for function in raw_function.splitlines() if function.strip() and not function.strip().startswith("#")]

    def __str__(self) -> str:
        return self._raw_function

    def __repr__(self) -> str:
        return f"Function(name={self._name}, domain={self._domain}, codomain={self._codomain})"

    def evaluate(self, *n: float) -> float:
        if len(n) != self.get_amount_of_arguments():
            raise ValueError(f"Expected {self.get_amount_of_arguments()} arguments, got {len(n)}")
        local_namespace = Namespace(f"{self.name}_evaluation")
        for var, value in zip(self._argument_variables, n):
            local_namespace.add_variable(var, value)
        return self._function_ast.evaluate(local_namespace)


if __name__ == "__main__":
    functions = Function.from_file("example_function")
    print(functions)

