from __future__ import annotations

from dataclasses import dataclass

from Core.Function.FunctionInterpreter.ASTNodes import ExpressionNode, ProductNode, SummationNode


@dataclass
class _AggregateFunction:
    name: str

    @property
    def argument_variables(self) -> list[str]:
        return ["bound", "start", "end", "body"]

    def get_amount_of_arguments(self) -> int:
        return 4

    def check_domain(self, *values):
        return None

    def evaluate(self, *values):
        raise NotImplementedError("Aggregate functions are handled structurally, not by direct scalar evaluation")

    def build_node(self, arguments: tuple[ExpressionNode, ...]) -> ExpressionNode:
        raise NotImplementedError


class Sigma(_AggregateFunction):
    def __init__(self):
        super().__init__("sigma")

    def build_node(self, arguments: tuple[ExpressionNode, ...]) -> ExpressionNode:
        if len(arguments) != 4:
            raise ValueError("sigma requires four arguments")
        bound, start, end, body = arguments
        from Core.Function.FunctionInterpreter.ASTNodes import IdentifierNode

        if not isinstance(bound, IdentifierNode):
            raise ValueError("sigma bound variable must be an identifier")
        return SummationNode(bound.name, start, end, body)


class Pi(_AggregateFunction):
    def __init__(self):
        super().__init__("pi")

    def build_node(self, arguments: tuple[ExpressionNode, ...]) -> ExpressionNode:
        if len(arguments) != 4:
            raise ValueError("pi requires four arguments")
        bound, start, end, body = arguments
        from Core.Function.FunctionInterpreter.ASTNodes import IdentifierNode

        if not isinstance(bound, IdentifierNode):
            raise ValueError("pi bound variable must be an identifier")
        return ProductNode(bound.name, start, end, body)
