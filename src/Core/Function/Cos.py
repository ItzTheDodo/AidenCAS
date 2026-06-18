import math

from Core.Function.UnaryTrigFunction import UnaryTrigFunction


class Cos(UnaryTrigFunction):
    """Builtin cosine function."""
    function_name = "cos"
    evaluate_fn = staticmethod(math.cos)
    derivative_expression = "-sin(x)"
    inverse_expression = "acos({y})"

    def __str__(self) -> str:
        return "cos(x)"