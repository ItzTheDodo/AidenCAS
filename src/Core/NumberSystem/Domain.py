from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Domain(ABC):
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def contains(self, value: Any) -> bool:
        raise NotImplementedError

    def __contains__(self, value: Any) -> bool:
        return self.contains(value)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name})"
