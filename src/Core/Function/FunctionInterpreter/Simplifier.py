from __future__ import annotations

from dataclasses import dataclass, field

from Core.Function.FunctionInterpreter.ASTNodes import ExpressionNode, SimplificationContext
from Core.Function.FunctionInterpreter.FunctionAST import FunctionAST


@dataclass(frozen=True)
class Simplifier:
    """Thin orchestration layer that applies node-level simplification."""
    context: SimplificationContext = field(default_factory=SimplificationContext)

    def simplify_node(self, node: ExpressionNode) -> ExpressionNode:
        """Delegate simplification to the node itself."""
        return node.simplify(self.context)

    def simplify_ast(self, ast: FunctionAST) -> FunctionAST:
        """Return a new AST whose root has been simplified."""
        return FunctionAST(self.simplify_node(ast.root))
