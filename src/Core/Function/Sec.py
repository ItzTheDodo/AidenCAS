from __future__ import annotations

import math

from Core.Function.UnaryTrigFunction import UnaryTrigFunction


class Sec(UnaryTrigFunction):
    function_name = "sec"
    evaluate_fn = staticmethod(lambda x: 1 / math.cos(x))
    derivative_expression = "sec(x)*tan(x)"
    inverse_expression = "acos(1/{y})"

    def __str__(self) -> str:
        return "sec(x)"

