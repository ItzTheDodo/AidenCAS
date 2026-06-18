from __future__ import annotations

import math
from typing import TYPE_CHECKING, Callable

from Core.Function.FunctionInterpreter.Function import Function

if TYPE_CHECKING:
    from Core.Namespace.Namespace import Namespace


class UnaryTrigFunction(Function):
    function_name: str = ""
    evaluate_fn: Callable[[float], float] = staticmethod(lambda x: x)
    derivative_expression: str = ""
    inverse_expression: str | None = None

    def __init__(self, namespace: Namespace | None = None):
        super().__init__(f"{self.function_name}: R -> R; x -> x", namespace)

    def evaluate(self, *n: float) -> float:
        if len(n) != 1:
            raise ValueError(f"Expected 1 argument, got {len(n)}")
        self.check_domain(n[0])
        return self.evaluate_fn(float(n[0]))

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
            Function(
                f"{self.name}_d_{variable}: R -> R; x -> {self.derivative_expression}",
                self.namespace,
            ),
        )

    def partial_derivative(self, variable: str) -> Function:
        return self.derivative(variable)

    def simplify(self) -> Function:
        return self

    def inverse(self, value_name: str = "y") -> Function:
        if self.inverse_expression is None:
            raise NotImplementedError(f"Inverse for {self.function_name} is not implemented")
        return Function(f"{self.name}_inverse: R -> R; {value_name} -> {self.inverse_expression.format(y=value_name)}", self.namespace)

