from __future__ import annotations

import math

from Core.Function.UnaryTrigFunction import UnaryTrigFunction


class Cot(UnaryTrigFunction):
    function_name = "cot"
    evaluate_fn = staticmethod(lambda x: 1 / math.tan(x))
    derivative_expression = "-csc(x)^2"
    inverse_expression = "atan(1/{y})"

    def __str__(self) -> str:
        return "cot(x)"

