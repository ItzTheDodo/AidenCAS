from Core.Function.BinaryOperations.BinaryOperation import BinaryOperation
from Core.Set.Set import Set


class Group:

    def __init__(self, set_: Set, operation: BinaryOperation):

        self._set = set_
        self._operation = operation

        self._operation.set = self.set

    @property
    def set(self) -> Set:
        return self._set

    @property
    def operation(self) -> BinaryOperation:
        return self._operation
