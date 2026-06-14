from __future__ import annotations

import math

from typing import TYPE_CHECKING

from Core.Function.FunctionInterpreter.Function import Function

if TYPE_CHECKING:
    from Core.Namespace.Namespace import Namespace


class Logarithm(Function):
    """Builtin natural logarithm function log(x)."""

    def __init__(self, namespace: Namespace | None = None):
        super().__init__("log: R+ -> R; x -> x", namespace)

    def evaluate(self, *n: float) -> float:
        if len(n) != 1:
            raise ValueError(f"Expected 1 argument, got {len(n)}")
        self.check_domain(n[0])
        return math.log(n[0])

    def derivative(self, variable: str) -> Function:
        if variable not in self.argument_variables:
            raise ValueError(f"Unknown differentiation variable: {variable}")
        cached_function = self.namespace.get_cached_derivative(self.name, variable, "_d")
        if cached_function is not None:
            return cached_function
        return self.namespace.cache_derivative(
            self.name,
            variable,
            "_d",
            Function(f"{self.name}_d_{variable}: R+ -> R; x -> 1/x", self.namespace),
        )

    def partial_derivative(self, variable: str) -> Function:
        return self.derivative(variable)

    def inverse(self, value_name: str = "y") -> Function:
        return Function(f"{self.name}_inverse: R -> R+; {value_name} -> exp({value_name})", self.namespace)

    def simplify(self) -> Function:
        return self

    def __str__(self) -> str:
        return "log(x)"
