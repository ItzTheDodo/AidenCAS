import math

from Core.Function.UnaryTrigFunction import UnaryTrigFunction


class ACos(UnaryTrigFunction):
    """Builtin arc cosine function."""
    function_name = "acos"
    evaluate_fn = staticmethod(math.acos)
    derivative_expression = "-1/((1 - x^2)^0.5)"
    inverse_expression = "cos({y})"

    def __str__(self) -> str:
        return "acos(x)"
