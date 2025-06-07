from __future__ import annotations
from typing import Iterable

from pydantic import BaseModel
from abc import ABC


class Formula(ABC, BaseModel):
    """Base class for all LTL formulas."""

    def child_formulas(self) -> Iterable[Formula]:
        yield from []

    def subformulas(self) -> Iterable[Formula]:
        yield self
        for child_forumla in self.child_formulas():
            yield from child_forumla.subformulas()

    def values(self) -> Iterable[Value]:
        """Recursively yield all Value instances contained in the formula."""
        for child_formula in self.child_formulas():
            yield from child_formula.values()


class Value(ABC, BaseModel):
    """Base class for all values in LTL formulas."""


class Variable(Value):
    """Class representing a variable in LTL formulas."""

    name: str

    def __str__(self) -> str:
        return self.name


class Atom(Value):
    """Class representing a constant value in LTL formulas."""

    value: str

    def __str__(self) -> str:
        return self.value


class Equal(Formula):
    """Class representing an equality formula."""

    left: Value
    right: Value

    def values(self) -> Iterable[Value]:
        yield self.left
        yield self.right

    def __str__(self) -> str:
        return f"{self.left} = {self.right}"


class Bool(Formula):
    value: bool

    def __str__(self) -> str:
        return str(self.value).lower()


class And(Formula):
    left: Formula
    right: Formula

    def child_formulas(self) -> Iterable[Formula]:
        yield self.left
        yield self.right

    def __str__(self) -> str:
        return f"({self.left} ∧ {self.right})"


class Or(Formula):
    left: Formula
    right: Formula

    def child_formulas(self) -> Iterable[Formula]:
        yield self.left
        yield self.right

    def __str__(self) -> str:
        return f"({self.left} ∨ {self.right})"


class Not(Formula):
    operand: Formula

    def child_formulas(self) -> Iterable[Formula]:
        yield self.operand

    def __str__(self) -> str:
        return f"¬{self.operand}"


class Implies(Formula):
    antecedent: Formula
    consequent: Formula

    def child_formulas(self) -> Iterable[Formula]:
        yield self.antecedent
        yield self.consequent

    def __str__(self) -> str:
        return f"({self.antecedent} → {self.consequent})"


class Predicate(Formula):
    name: str
    args: list[Value] = []

    def values(self) -> Iterable[Value]:
        yield from self.args

    def __str__(self) -> str:
        if self.args:
            return f"{self.name}({', '.join(str(arg) for arg in self.args)})"
        return self.name

    @property
    def is_atomic(self) -> bool:
        """Check if the predicate is atomic (no arguments)."""
        return len(self.args) == 0


class Next(Formula):
    operand: Formula

    def child_formulas(self) -> Iterable[Formula]:
        yield self.operand

    def __str__(self) -> str:
        return f"X{self.operand}"


class Until(Formula):
    left: Formula
    right: Formula

    def child_formulas(self) -> Iterable[Formula]:
        yield self.left
        yield self.right

    def __str__(self) -> str:
        return f"({self.left} U {self.right})"


class Future(Formula):
    operand: Formula

    def child_formulas(self) -> Iterable[Formula]:
        yield self.operand

    def __str__(self) -> str:
        return f"F{self.operand}"


class Global(Formula):
    operand: Formula

    def child_formulas(self) -> Iterable[Formula]:
        yield self.operand

    def __str__(self) -> str:
        return f"G{self.operand}"


basis_operators: list[type[Formula]] = [Next, Until, Global, Not, And, Bool]
"""A list of operators that form a basis: all LTL formulas can be expressed using _only_ these operators.

The Boolean fragment basis (Not, And, Bool) is standard. The temporal fragment is not technically a basis (Global can be rewritten using Until), but because we'll be analyzing finite traces we will often need to rely on weak Until, which is not strong enough to capture the behavior of Global.
"""


def normalize_root_formula(formula: Formula) -> Formula:
    """Normalize the root formula to ensure it doesn't use any operators outside the basis.

    Does not recurse into any child formulas.
    """
    match formula:
        # Simplify via De Morgan's Law, so A or B -> !(!A and !B)
        case Or(left=left, right=right):
            return Not(operand=And(left=Not(operand=left), right=Not(operand=right)))

        # Translate to OR using material implication (then apply De Morgan's Laws):
        # A => B -> !A or B -> !(A and !B)
        case Implies(antecedent=antecedent, consequent=consequent):
            return Not(operand=And(left=antecedent, right=Not(operand=consequent)))

        # Future
        case Future(operand=operand):
            return Until(left=Bool(value=True), right=operand)

        case _:
            return formula
