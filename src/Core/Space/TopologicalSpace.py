from Core.Set.Set import Set


class TopologicalSpace:

    def __init__(self, elements: Set):

        self._elements = elements

    @property
    def elements(self) -> Set:
        return self._elements

