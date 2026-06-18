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

## Trigonometric builtins

The namespace now includes `sin`, `cos`, `tan`, `cot`, `sec`, `csc`, `asin`, `acos`, and `atan`.

Common simplifications include:

- `sin(asin(x)) -> x`
- `cos(acos(x)) -> x`
- `tan(atan(x)) -> x`
- `sin(-x) -> -sin(x)`
- `cos(-x) -> cos(x)`
- `sin(x)^2 + cos(x)^2 -> 1`
- `1 + tan(x)^2 -> sec(x)^2`
- `1 + cot(x)^2 -> csc(x)^2`
- `sec(x)^2 - tan(x)^2 -> 1`
- `csc(x)^2 - cot(x)^2 -> 1`

## Domains

Function definitions now resolve their `domain -> codomain` names through namespace domain objects. That lets you register scalar sets, matrix spaces, or other algebraic structures before compiling a function.
