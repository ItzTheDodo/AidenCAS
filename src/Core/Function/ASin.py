import math

from Core.Function.UnaryTrigFunction import UnaryTrigFunction


class ASin(UnaryTrigFunction):
    """Builtin arc sine function."""
    function_name = "asin"
    evaluate_fn = staticmethod(math.asin)
    derivative_expression = "1/((1 - x^2)^0.5)"
    inverse_expression = "sin({y})"

    def __str__(self) -> str:
        return "asin(x)"