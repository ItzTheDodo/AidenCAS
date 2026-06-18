from __future__ import annotations

import math

from Core.Function.UnaryTrigFunction import UnaryTrigFunction


class ATan(UnaryTrigFunction):
    function_name = "atan"
    evaluate_fn = staticmethod(math.atan)
    derivative_expression = "1/(1+x^2)"
    inverse_expression = "tan({y})"

    def __str__(self) -> str:
        return "atan(x)"

