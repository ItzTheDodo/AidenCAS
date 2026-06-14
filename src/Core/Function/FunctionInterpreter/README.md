# Function interpreter

This package turns source expressions into immutable ASTs and then rewrites them.

## Main pieces

- `FunctionAST` — tokenizer, parser, and AST wrapper.
- `ASTNodes` — expression node types and simplification/evaluation logic.
- `Rearranger` — symbolic isolation engine used by `Function.rearrange()`.
- `LexicalBlocks/` — token classes used during parsing.

## Expression grammar

Supported core syntax includes:

- literals and identifiers
- binary operators: `+`, `-`, `*`, `/`, `^`
- unary negation: `-x`
- function calls: `f(x, y)`
- aggregates: `sigma(i, a, b, body)` and `pi(i, a, b, body)` as callable builtin functions
- matrix literals: `[[1,2],[3,4]]` (parsed into `Core.Matrix.Matrix`)

## AST node families

- `LiteralNode` — scalar values or `Matrix` objects
- `IdentifierNode` — variable references
- `UnaryOperationNode` — negation
- `BinaryOperationNode` — arithmetic operators
- `FunctionCallNode` — builtin or user-defined function calls
- `SummationNode` / `ProductNode` — finite aggregate expressions

## Simplification

The AST uses node-local simplification to:

- fold constant subexpressions
- normalize additive and multiplicative terms
- collapse trivial identities
- expand finite aggregates when bounds are concrete

## Rearrangement

The rearranger can isolate a chosen subject variable for supported forms and is used by:

- `Function.inverse()`
- `Function.rearrange()`
- `Function.rearrange_to_constant()`
