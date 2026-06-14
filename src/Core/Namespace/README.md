# Namespace subsystem

`Namespace` is the registry used by the parser and evaluator.

## Responsibilities

- Store variables and their runtime values.
- Store named domains used for domain checking.
- Store builtin and user-defined functions.
- Store binary operations used by the expression parser.
- Cache derivative functions.

## Default registrations

By default a namespace loads:

- scalar domains: `|N`, `Z`, `|Z`, `Q`, `|Q`, `R`, `|R`, `R+`, `LWdom`
- matrix domains: `M2(R)`, `GL2(R)`
- binary operations: `+`, `-`, `*`, `/`, `^`
- builtin functions: `exp`, `lambertw`, `log`, `sigma`, `pi`

`add_set()` still works as a compatibility shortcut for scalar domains, while `add_domain()` is the OO path.

## Deferred functions

If the parser sees a function call before the definition exists, the namespace can reserve a deferred placeholder. That lets forward references parse cleanly until the real function is registered.
