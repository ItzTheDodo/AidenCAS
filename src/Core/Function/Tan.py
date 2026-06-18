from __future__ import annotations

import math

from Core.Function.UnaryTrigFunction import UnaryTrigFunction


class Tan(UnaryTrigFunction):
    function_name = "tan"
    evaluate_fn = staticmethod(math.tan)
    derivative_expression = "sec(x)^2"
    inverse_expression = "atan({y})"

    def __str__(self) -> str:
        return "tan(x)"

