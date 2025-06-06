from __future__ import annotations

from pydantic import BaseModel
from abc import ABC

class Formula(ABC, BaseModel):
    """Base class for all LTL formulas."""

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

    def __str__(self) -> str:
        return f"{self.left} = {self.right}"

class Bool(Formula):
    value: bool

    def __str__(self) -> str:
        return str(self.value).lower()

class And(Formula):
    left: Formula
    right: Formula

    def __str__(self) -> str:
        return f"({self.left} ∧ {self.right})"

class Or(Formula):
    left: Formula
    right: Formula

    def __str__(self) -> str:
        return f"({self.left} ∨ {self.right})"

class Not(Formula):
    operand: Formula

    def __str__(self) -> str:
        return f"¬{self.operand}"

class Implies(Formula):
    antecedent: Formula
    consequent: Formula

    def __str__(self) -> str:
        return f"({self.antecedent} → {self.consequent})"

class Predicate(Formula):
    name: str
    args: list[Value] = []

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

    def __str__(self) -> str:
        return f"X{self.operand}"

class Until(Formula):
    left: Formula
    right: Formula

    def __str__(self) -> str:
        return f"({self.left} U {self.right})"

class Future(Formula):
    operand: Formula

    def __str__(self) -> str:
        return f"F{self.operand}"

class Global(Formula):
    operand: Formula

    def __str__(self) -> str:
        return f"G{self.operand}"
