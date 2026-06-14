from __future__ import annotations

from typing import Any

from Core.Matrix.Matrix import Matrix
from Core.NumberSystem.Domain import Domain
from Core.Set.Set import Set


class ScalarDomain(Domain):
    def __init__(self, name: str, set_: Set):
        super().__init__(name)
        self._set = set_

    @property
    def set(self) -> Set:
        return self._set

    def _contains_scalar(self, value: Any) -> bool:
        if hasattr(self._set, "contains"):
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return bool(self._set.contains(float(value)))
            return bool(self._set.contains(value))
        return value in self._set

    def contains(self, value: Any) -> bool:
        if isinstance(value, Matrix):
            return all(self._contains_scalar(item) for row in value.rows for item in row)
        if isinstance(value, (list, tuple)) and value and any(isinstance(item, (list, tuple, Matrix)) for item in value):
            return all(self.contains(item) for item in value)
        return self._contains_scalar(value)
