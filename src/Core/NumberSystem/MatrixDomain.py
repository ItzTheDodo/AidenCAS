from __future__ import annotations

from typing import Any

from Core.Matrix.Matrix import Matrix
from Core.NumberSystem.Domain import Domain
from Core.NumberSystem.ScalarDomain import ScalarDomain
from Core.Set.Interval import Interval
from Core.Set.IntervalSet import IntervalSet


class MatrixDomain(Domain):
    def __init__(self, name: str, rows: int, cols: int | None = None, element_domain: Domain | None = None, invertible: bool = False):
        super().__init__(name)
        self._rows = rows
        self._cols = cols if cols is not None else rows
        self._element_domain = element_domain if element_domain is not None else ScalarDomain("R", IntervalSet(Interval(float("-inf"), float("inf"), True, True)))
        self._invertible = invertible

    @property
    def shape(self) -> tuple[int, int]:
        return self._rows, self._cols

    @property
    def element_domain(self) -> Domain:
        return self._element_domain

    def contains(self, value: Any) -> bool:
        if isinstance(value, (list, tuple)):
            try:
                value = Matrix.from_nested(value)
            except Exception:
                return False
        if not isinstance(value, Matrix):
            return False
        if value.shape != self.shape:
            return False
        if not all(self.element_domain.contains(item) for row in value.rows for item in row):
            return False
        if self._invertible:
            if self._rows != self._cols:
                return False
            return value.determinant() != 0
        return True
