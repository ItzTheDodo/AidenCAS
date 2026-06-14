from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _format_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    text = f"{value:.17f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


@dataclass(frozen=True)
class Matrix:
    rows: tuple[tuple[Any, ...], ...]

    def __post_init__(self):
        if not self.rows:
            raise ValueError("Matrix cannot be empty")
        width = len(self.rows[0])
        if width == 0:
            raise ValueError("Matrix rows cannot be empty")
        if any(len(row) != width for row in self.rows):
            raise ValueError("Matrix rows must all have the same length")

    @property
    def shape(self) -> tuple[int, int]:
        return len(self.rows), len(self.rows[0])

    def _map(self, fn) -> Matrix:
        return Matrix(tuple(tuple(fn(value) for value in row) for row in self.rows))

    def add(self, other: Matrix | float) -> Matrix:
        if isinstance(other, Matrix):
            if self.shape != other.shape:
                raise ValueError("Matrix addition requires matching shapes")
            return Matrix(
                tuple(
                    tuple(self.rows[i][j] + other.rows[i][j] for j in range(self.shape[1]))
                    for i in range(self.shape[0])
                )
            )
        if _is_number(other):
            return self._map(lambda value: value + float(other))
        raise TypeError(f"Unsupported matrix addition with {type(other).__name__}")

    def subtract(self, other: Matrix | float) -> Matrix:
        if isinstance(other, Matrix):
            if self.shape != other.shape:
                raise ValueError("Matrix subtraction requires matching shapes")
            return Matrix(
                tuple(
                    tuple(self.rows[i][j] - other.rows[i][j] for j in range(self.shape[1]))
                    for i in range(self.shape[0])
                )
            )
        if _is_number(other):
            return self._map(lambda value: value - float(other))
        raise TypeError(f"Unsupported matrix subtraction with {type(other).__name__}")

    def multiply(self, other: Matrix | float) -> Matrix:
        if _is_number(other):
            return self._map(lambda value: value * float(other))
        if isinstance(other, Matrix):
            left_rows, left_cols = self.shape
            right_rows, right_cols = other.shape
            if left_cols != right_rows:
                raise ValueError("Matrix multiplication requires compatible dimensions")
            result_rows: list[tuple[Any, ...]] = []
            for row_index in range(left_rows):
                result_row: list[Any] = []
                for col_index in range(right_cols):
                    total = 0.0
                    for inner_index in range(left_cols):
                        total += self.rows[row_index][inner_index] * other.rows[inner_index][col_index]
                    result_row.append(total)
                result_rows.append(tuple(result_row))
            return Matrix(tuple(result_rows))
        raise TypeError(f"Unsupported matrix multiplication with {type(other).__name__}")

    def divide(self, other: float) -> Matrix:
        if not _is_number(other):
            raise TypeError(f"Unsupported matrix division with {type(other).__name__}")
        if float(other) == 0:
            raise ZeroDivisionError("Division by zero")
        return self._map(lambda value: value / float(other))

    def power(self, exponent: float) -> Matrix:
        if not _is_number(exponent):
            raise TypeError(f"Unsupported matrix power with {type(exponent).__name__}")
        power = int(exponent)
        if power != exponent or power < 0:
            raise ValueError("Matrix powers require a non-negative integer exponent")
        rows, cols = self.shape
        if rows != cols:
            raise ValueError("Matrix powers require square matrices")
        if power == 0:
            return Matrix(tuple(tuple(1.0 if i == j else 0.0 for j in range(cols)) for i in range(rows)))
        result = self
        for _ in range(power - 1):
            result = result.multiply(self)
        return result

    def determinant(self) -> float:
        rows, cols = self.shape
        if rows != cols:
            raise ValueError("Determinant requires a square matrix")

        data = [[float(value) for value in row] for row in self.rows]
        det = 1.0
        sign = 1.0

        for pivot_index in range(rows):
            pivot_row = None
            for candidate in range(pivot_index, rows):
                if data[candidate][pivot_index] != 0:
                    pivot_row = candidate
                    break

            if pivot_row is None:
                return 0.0

            if pivot_row != pivot_index:
                data[pivot_index], data[pivot_row] = data[pivot_row], data[pivot_index]
                sign *= -1

            pivot = data[pivot_index][pivot_index]
            det *= pivot
            for row_index in range(pivot_index + 1, rows):
                factor = data[row_index][pivot_index] / pivot
                for col_index in range(pivot_index, cols):
                    data[row_index][col_index] -= factor * data[pivot_index][col_index]

        return sign * det

    def negate(self) -> Matrix:
        return self._map(lambda value: -value)

    def to_expression(self) -> str:
        return "[" + ",".join("[" + ",".join(_format_number(float(value)) for value in row) + "]" for row in self.rows) + "]"

    def signature(self) -> str:
        return self.to_expression()

    @classmethod
    def from_nested(cls, value) -> Matrix:
        if not value:
            raise ValueError("Matrix cannot be empty")
        rows = []
        width = len(value[0])
        for row in value:
            if len(row) != width:
                raise ValueError("Matrix rows must all have the same length")
            rows.append(tuple(float(item) if _is_number(item) else item for item in row))
        return cls(tuple(rows))
