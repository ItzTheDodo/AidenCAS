from __future__ import annotations

import math

from typing import TYPE_CHECKING

from Core.Function.FunctionInterpreter.Function import Function

if TYPE_CHECKING:
    from Core.Namespace.Namespace import Namespace


class LambertW(Function):
    """Builtin principal Lambert W function."""

    def __init__(self, namespace: Namespace | None = None):
        super().__init__("lambertw: LWdom -> R; x -> x", namespace)

    def evaluate(self, *n: float) -> float:
        if len(n) != 1:
            raise ValueError(f"Expected 1 argument, got {len(n)}")
        self.check_domain(n[0])
        x = float(n[0])
        if x == 0:
            return 0.0

        if x < -1 / math.e:
            raise ValueError("Lambert W is undefined on the real branch for x < -1/e")

        w = math.log1p(x) if x > 1 else x
        for _ in range(100):
            ew = math.exp(w)
            f = w * ew - x
            denom = ew * (w + 1)
            if abs(denom) < 1e-15:
                break
            next_w = w - f / denom
            if abs(next_w - w) <= 1e-12:
                return next_w
            w = next_w
        return w

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
                f"{self.name}_d_{variable}: LWdom -> R; x -> lambertw(x)/(x*(1+lambertw(x)))",
                self.namespace,
            ),
        )

    def partial_derivative(self, variable: str) -> Function:
        return self.derivative(variable)

    def inverse(self, value_name: str = "y") -> Function:
        return Function(f"{self.name}_inverse: R -> R; {value_name} -> {value_name}*exp({value_name})", self.namespace)

    def simplify(self) -> Function:
        return self

    def __str__(self) -> str:
        return "lambertw(x)"
