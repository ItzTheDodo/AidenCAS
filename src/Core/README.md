# Core

This directory contains the symbolic math core used by AidenCAS.

## Subsystems

- `Function/` — symbolic functions, parsing, simplification, derivatives, rearrangement, and builtins.
- `Set/` — interval, finite, integer, rational, and natural-number domain/set models.
- `Namespace/` — registry for domains, functions, binary operations, and cached derivatives.
- `NumberSystem/` — light algebraic wrappers for groups and rings.
- `Space/` — basic topological-space wrapper.

## What the core currently supports

- Scalar expressions with `+`, `-`, `*`, `/`, `^`, unary negation, and function calls.
- Builtin functions such as `exp`, `log`, `lambertw`, and the trig suite.
- Symbolic differentiation and rearrangement/inversion for supported forms.
- Aggregate expressions with `sigma(...)` and `pi(...)`.
- Domain-object based checking, including scalar sets and matrix spaces.
- General literal leaves, including matrix literals backed by a dedicated `Matrix` object.

## Recommended entry points

- `Core.Function.FunctionInterpreter.Function.Function`
- `Core.Namespace.Namespace.Namespace`
- `Core.Set.IntervalSet.IntervalSet`
- `Core.Set.FiniteSet.FiniteSet`
