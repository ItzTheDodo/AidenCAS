from Core.Function.BinaryOperations.BinaryOperation import BinaryOperation
from Core.NumberSystem.Group import Group
from Core.Set.FiniteSet import FiniteSet
from Core.Set.Interval import Interval
from Core.Set.Set import Set


class Ring:

    def __init__(self, set_: Set, add_operation: BinaryOperation, mul_operation: BinaryOperation):

        self._set = set_
        self._additive_group = Group(self._set, add_operation)
        self._mul_operation = mul_operation

    @property
    def set(self) -> Set:
        return self._set

    @property
    def additive_group(self) -> Group:
        return self._additive_group

    @property
    def mul_operation(self) -> BinaryOperation:
        return self._mul_operation

    @property
    def zero_divisors(self) -> Set:
        S_without_zero = self.set.without(FiniteSet(self.mul_operation.zero))
        preimage = self.mul_operation.transform_set_right(S_without_zero, self.mul_operation.zero)
        out = self.set.intersect(preimage)
        if out.is_singleton():
            return FiniteSet(out.get_singleton_element())
        return out

    @property
    def units(self) -> Set:
        if self.mul_operation.identity not in self.set:
            raise ValueError("Multiplicative identity must be in the set for units to be defined.")

        # If the underlying set is finite we can brute-force search for inverses
        if hasattr(self._set, "elements"):
            elements = list(self._set.elements)
            unit_elements: list[float] = []
            for a in elements:
                # skip zero
                if a == self.mul_operation.zero:
                    continue

                # search for a right-inverse (and left-inverse if noncommutative)
                found_inverse = False
                for b in elements:
                    try:
                        ab = self.mul_operation.calculate(a, b)
                    except Exception:
                        continue

                    if ab != self.mul_operation.identity:
                        continue

                    # if multiplication is not commutative, require the other side too
                    if not self.mul_operation.commutative:
                        try:
                            ba = self.mul_operation.calculate(b, a)
                        except Exception:
                            continue
                        if ba != self.mul_operation.identity:
                            continue

                    found_inverse = True
                    break

                if found_inverse:
                    unit_elements.append(a)

            return FiniteSet(*unit_elements)

        unit_elements = []
        if hasattr(self._set, "elements"):
            for x in self._set.elements:
                if x == self.mul_operation.zero:
                    continue
                inv = self.mul_operation.invert(x)
                if inv is not None and inv in self._set:
                    unit_elements.append(x)
            return FiniteSet(*unit_elements)

        S_without_zero = self.set.without(FiniteSet(self.mul_operation.zero))
        inverse_S = self.mul_operation.invert(S_without_zero)
        if inverse_S is None:
            return FiniteSet(0) # No units if no inverses exist
        out = self.set.intersect(inverse_S)
        if out.is_singleton():
            return FiniteSet(out.get_singleton_element())
        return out

    def is_integral_domain(self) -> bool:
        return self.zero_divisors.is_empty()

    def is_division_ring(self) -> bool:
        return self.units == self.set.without(FiniteSet(self.mul_operation.zero))

    def is_field(self) -> bool:
        return self.is_division_ring() and self.is_integral_domain()


if __name__ == "__main__":
    from Core.Set.Integers import Integers
    from Core.Function.BinaryOperations.Addition import Addition
    from Core.Function.BinaryOperations.Multiplication import Multiplication

    Z = Ring(Integers(Interval(float("-inf"), float("inf"), True, True)), Addition(), Multiplication())
    print(Z.zero_divisors)
    print(Z.units)
    # print(Z.is_integral_domain())
    # print(Z.is_division_ring())
    # print(Z.is_field())