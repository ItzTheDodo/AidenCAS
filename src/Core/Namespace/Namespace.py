from __future__ import annotations

from Core.Function.BinaryOperations.Addition import Addition
from Core.Function.BinaryOperations.BinaryOperation import BinaryOperation
from Core.Function.BinaryOperations.Multiplication import Multiplication
from Core.Set.Integers import Integers
from Core.Set.Interval import Interval
from Core.Set.IntervalSet import IntervalSet
from Core.Set.NaturalNumbers import NaturalNumbers
from Core.Set.Rationals import Rationals
from Core.Set.Set import Set

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Core.Function.FunctionInterpreter.Function import Function


class Namespace:

    def __init__(self, name: str, load_defaults: bool = True):

        self._name = name
        self._variables: dict[str, float] = {}
        self._sets: dict[str, Set] = {}
        self._sub_spaces: dict[str, Namespace] = {}
        self._functions: dict[str, Function] = {}
        self._binary_operations: dict[str, BinaryOperation] = {}

        if load_defaults:
            self.load_defaults()

    def load_defaults(self):
        self.add_set("|N", NaturalNumbers())
        self.add_set("Z", Integers())
        self.add_set("|Z", Integers())
        self.add_set("|Q", Rationals())
        self.add_set("Q", Rationals())
        self.add_set("R", IntervalSet(Interval(float("-inf"), float("inf"), True, True)))
        self.add_set("|R", IntervalSet(Interval(float("-inf"), float("inf"), True, True)))

        self.add_binary_operation(Addition().name, Addition())
        self.add_binary_operation(Multiplication().name, Multiplication())

    def clear(self):
        self._variables.clear()
        self._sets.clear()
        self._sub_spaces.clear()
        self._functions.clear()

    @property
    def name(self) -> str:
        return self._name

    def add_variable(self, name: str, value: float):
        self._variables[name] = value

    def add_set(self, name: str, set_: Set):
        self._sets[name] = set_

    def add_sub_space(self, name: str, sub_space: Namespace):
        self._sub_spaces[name] = sub_space

    def add_function(self, name: str, function: Function):
        self._functions[name] = function

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

    def remove_binary_operation(self, name: str):
        if name in self._binary_operations:
            del self._binary_operations[name]

    @property
    def variables(self) -> dict[str, float]:
        return self._variables

    @property
    def sets(self) -> dict[str, Set]:
        return self._sets

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
