import math

from Core.Function.UnaryTrigFunction import UnaryTrigFunction


class Sin(UnaryTrigFunction):
    """Builtin sine function."""
    function_name = "sin"
    evaluate_fn = staticmethod(math.sin)
    derivative_expression = "cos(x)"
    inverse_expression = "asin({y})"

    def __str__(self) -> str:
        return "sin(x)"
