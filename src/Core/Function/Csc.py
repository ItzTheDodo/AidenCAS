from __future__ import annotations

import math

from Core.Function.UnaryTrigFunction import UnaryTrigFunction


class Csc(UnaryTrigFunction):
    function_name = "csc"
    evaluate_fn = staticmethod(lambda x: 1 / math.sin(x))
    derivative_expression = "-csc(x)*cot(x)"
    inverse_expression = "asin(1/{y})"

    def __str__(self) -> str:
        return "csc(x)"

