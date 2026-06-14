from __future__ import annotations

import math
from typing import Any

from Core.Function.BinaryOperations.Addition import Addition
from Core.Function.BinaryOperations.BinaryOperation import BinaryOperation
from Core.Function.BinaryOperations.Division import Division
from Core.Function.BinaryOperations.Multiplication import Multiplication
from Core.Function.BinaryOperations.Power import Power
from Core.Function.BinaryOperations.Subtraction import Subtraction
from Core.NumberSystem.Domain import Domain
from Core.NumberSystem.MatrixDomain import MatrixDomain
from Core.NumberSystem.ScalarDomain import ScalarDomain
from Core.Set.Integers import Integers
from Core.Set.Interval import Interval
from Core.Set.IntervalSet import IntervalSet
from Core.Set.NaturalNumbers import NaturalNumbers
from Core.Set.Rationals import Rationals
from Core.Set.Set import Set

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Core.Function.FunctionInterpreter.Function import Function


class _DeferredFunction:
    """Placeholder that resolves to a real function once it is compiled."""

    def __init__(self, name: str):
        self._name = name
        self._target: Function | None = None

    @property
    def name(self) -> str:
        return self._name

    def bind(self, function: Function) -> None:
        self._target = function

    @property
    def target(self) -> Function:
        if self._target is None:
            raise ValueError(f"Function '{self._name}' has not been defined yet")
        return self._target

    @property
    def is_resolved(self) -> bool:
        return self._target is not None

    def __getattr__(self, item):
        return getattr(self.target, item)

    def __str__(self) -> str:
        return str(self.target) if self._target is not None else f"DeferredFunction({self._name})"

    def __repr__(self) -> str:
        return self.__str__()


class Namespace:

    def __init__(self, name: str, load_defaults: bool = True):

        self._name = name
        self._variables: dict[str, Any] = {}
        self._sets: dict[str, Set] = {}
        self._domains: dict[str, Domain] = {}
        self._sub_spaces: dict[str, Namespace] = {}
        self._functions: dict[str, Function] = {}
        self._binary_operations: dict[str, BinaryOperation] = {}
        self._derivative_cache: dict[tuple[str, str, str], Function] = {}

        if load_defaults:
            self.load_defaults()

    def load_defaults(self):
        from Core.Function.Exp import Exp
        from Core.Function.AggregateFunctions import Pi, Sigma
        from Core.Function.LambertW import LambertW
        from Core.Function.Logarithm import Logarithm

        self.add_set("|N", NaturalNumbers())
        self.add_set("Z", Integers())
        self.add_set("|Z", Integers())
        self.add_set("|Q", Rationals())
        self.add_set("Q", Rationals())
        self.add_set("R", IntervalSet(Interval(float("-inf"), float("inf"), True, True)))
        self.add_set("|R", IntervalSet(Interval(float("-inf"), float("inf"), True, True)))
        self.add_set("R+", IntervalSet(Interval(0, float("inf"), True, True)))
        self.add_set("LWdom", IntervalSet(Interval(-1 / math.e, float("inf"), True, True)))
        self.add_domain("M2(R)", MatrixDomain("M2(R)", 2, 2))
        self.add_domain("GL2(R)", MatrixDomain("GL2(R)", 2, 2, invertible=True))

        self.add_binary_operation(Addition().name, Addition())
        self.add_binary_operation(Subtraction().name, Subtraction())
        self.add_binary_operation(Multiplication().name, Multiplication())
        self.add_binary_operation(Division().name, Division())
        self.add_binary_operation(Power().name, Power())

        Exp(self)
        LambertW(self)
        Logarithm(self)
        self.add_function("sigma", Sigma())
        self.add_function("pi", Pi())

    def clear(self):
        self._variables.clear()
        self._sets.clear()
        self._domains.clear()
        self._sub_spaces.clear()
        self._functions.clear()
        self._derivative_cache.clear()

    @property
    def name(self) -> str:
        return self._name

    def add_variable(self, name: str, value: Any):
        self._variables[name] = value

    def add_set(self, name: str, set_: Set):
        self._sets[name] = set_
        self._domains[name] = ScalarDomain(name, set_)

    def add_domain(self, name: str, domain: Domain):
        self._domains[name] = domain
        if isinstance(domain, ScalarDomain):
            self._sets[name] = domain.set

    def get_domain(self, name: str) -> Domain | None:
        return self._domains.get(name)

    def add_sub_space(self, name: str, sub_space: Namespace):
        self._sub_spaces[name] = sub_space

    def add_function(self, name: str, function: Function):
        existing = self._functions.get(name)
        if isinstance(existing, _DeferredFunction):
            existing.bind(function)
            self._functions[name] = existing
            return
        self._functions[name] = function

    def reserve_function(self, name: str):
        if name not in self._functions:
            self._functions[name] = _DeferredFunction(name)

    def add_binary_operation(self, name: str, binary_operation: BinaryOperation):
        self._binary_operations[name] = binary_operation

    def remove_variable(self, name: str):
        if name in self._variables:
            del self._variables[name]

    def remove_set(self, name: str):
        if name in self._sets:
            del self._sets[name]

    def remove_sub_space(self, name: str):
        if name in self._sub_spaces:
            del self._sub_spaces[name]

    def remove_function(self, name: str):
        if name in self._functions:
            del self._functions[name]

    def get_cached_derivative(self, function_name: str, variable: str, kind: str) -> Function | None:
        return self._derivative_cache.get((function_name, variable, kind))

    def cache_derivative(self, function_name: str, variable: str, kind: str, function: Function) -> Function:
        self._derivative_cache[(function_name, variable, kind)] = function
        return function

    def remove_binary_operation(self, name: str):
        if name in self._binary_operations:
            del self._binary_operations[name]

    @property
    def variables(self) -> dict[str, Any]:
        return self._variables

    @property
    def sets(self) -> dict[str, Set]:
        return self._sets

    @property
    def domains(self) -> dict[str, Domain]:
        return self._domains

    @property
    def sub_spaces(self) -> dict[str, Namespace]:
        return self._sub_spaces

    @property
    def functions(self) -> dict[str, Function]:
        return self._functions

    @property
    def binary_operations(self) -> dict[str, BinaryOperation]:
        return self._binary_operations

    def __str__(self) -> str:
        return f"Namespace( {self.name} )"

    def __repr__(self) -> str:
        return self.__str__()

    def is_in_binary_operation_namespace(self, char: str):
        return char in self._binary_operations.keys()

    def is_in_function_namespace(self, name: str):
        return name in self._functions.keys()
