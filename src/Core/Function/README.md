# Function subsystem

The function subsystem compiles user-facing function definitions into symbolic ASTs.

## Public surface

- `Function` — parse, evaluate, simplify, substitute, differentiate, and rearrange a named mapping.
- `Exp`, `Logarithm`, `LambertW` — builtin functions registered into a namespace.
- `BinaryOperations/` — arithmetic operators used by the parser and AST.
- `FunctionInterpreter/` — parser, AST nodes, simplifier hooks, and rearranger logic.

## Function definitions

Function sources follow the form:

```text
name: domain -> codomain; x, y -> expression
```

Examples:

```text
f: R -> R; x -> (x + 1)
g: R -> R; x, y -> (x*y)
h: R -> R; x -> sigma(i, 0, 5, (i*x))
```

## Capabilities

- Parse and render symbolic expressions.
- Evaluate against a namespace of variable values.
- Compute derivatives and partial derivatives.
- Substitute arguments with expressions or literals.
- Rearrange/invert supported expressions symbolically.
- Work with scalar literals, matrix literals, and callable aggregate builtins.

## Domains

Function definitions now resolve their `domain -> codomain` names through namespace domain objects. That lets you register scalar domains, matrix spaces, or other algebraic structures before compiling a function.
