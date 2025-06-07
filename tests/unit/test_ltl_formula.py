"""Unit tests for LTL formula normalization and iteration capabilities."""

from openhands.security.ltl.formula import (
    And,
    Atom,
    Bool,
    Equal,
    Future,
    Global,
    Implies,
    Next,
    Not,
    Or,
    Predicate,
    Until,
    Variable,
    normalize_root_formula,
)


class TestFormulaIteration:
    """Test iteration capabilities of Formula classes."""

    def test_child_formulas_base(self):
        """Test that base Formula returns empty iterator."""
        formula = Bool(value=True)
        assert list(formula.child_formulas()) == []

    def test_child_formulas_unary_operators(self):
        """Test child_formulas for unary operators."""
        inner = Bool(value=True)

        # Not
        not_formula = Not(operand=inner)
        assert list(not_formula.child_formulas()) == [inner]

        # Next
        next_formula = Next(operand=inner)
        assert list(next_formula.child_formulas()) == [inner]

        # Future
        future_formula = Future(operand=inner)
        assert list(future_formula.child_formulas()) == [inner]

        # Global
        global_formula = Global(operand=inner)
        assert list(global_formula.child_formulas()) == [inner]

    def test_child_formulas_binary_operators(self):
        """Test child_formulas for binary operators."""
        left = Bool(value=True)
        right = Bool(value=False)

        # And
        and_formula = And(left=left, right=right)
        assert list(and_formula.child_formulas()) == [left, right]

        # Or
        or_formula = Or(left=left, right=right)
        assert list(or_formula.child_formulas()) == [left, right]

        # Implies
        implies_formula = Implies(antecedent=left, consequent=right)
        assert list(implies_formula.child_formulas()) == [left, right]

        # Until
        until_formula = Until(left=left, right=right)
        assert list(until_formula.child_formulas()) == [left, right]

    def test_subformulas_simple(self):
        """Test subformulas method on simple formulas."""
        formula = Bool(value=True)
        subformulas = list(formula.subformulas())
        assert len(subformulas) == 1
        assert subformulas[0] == formula

    def test_subformulas_nested(self):
        """Test subformulas method on nested formulas."""
        inner = Bool(value=True)
        not_inner = Not(operand=inner)
        and_formula = And(left=not_inner, right=Bool(value=False))

        subformulas = list(and_formula.subformulas())
        assert len(subformulas) == 4
        # Should include: and_formula, not_inner, inner, Bool(False)
        assert and_formula in subformulas
        assert not_inner in subformulas
        assert inner in subformulas

    def test_subformulas_deep_nesting(self):
        """Test subformulas with deeply nested structure."""
        # Build: G(p -> F(q))
        p = Predicate(name='p')
        q = Predicate(name='q')
        f_q = Future(operand=q)
        implies = Implies(antecedent=p, consequent=f_q)
        global_formula = Global(operand=implies)

        subformulas = list(global_formula.subformulas())
        assert len(subformulas) == 5
        assert all(f in subformulas for f in [global_formula, implies, p, f_q, q])

    def test_values_empty(self):
        """Test values method on formulas without values."""
        formula = Bool(value=True)
        assert list(formula.values()) == []

    def test_values_equal(self):
        """Test values method on Equal formula."""
        var = Variable(name='x')
        atom = Atom(value='hello')
        equal = Equal(left=var, right=atom)

        values = list(equal.values())
        assert len(values) == 2
        assert values[0] == var
        assert values[1] == atom

    def test_values_predicate(self):
        """Test values method on Predicate formula."""
        args = [Variable(name='x'), Atom(value='42'), Variable(name='y')]
        pred = Predicate(name='foo', args=args)

        values = list(pred.values())
        assert values == args

    def test_values_nested(self):
        """Test values method with nested formulas."""
        x = Variable(name='x')
        y = Variable(name='y')
        eq1 = Equal(left=x, right=Atom(value='1'))
        eq2 = Equal(left=y, right=Atom(value='2'))
        and_formula = And(left=eq1, right=eq2)

        values = list(and_formula.values())
        assert len(values) == 4
        # Order matters based on traversal
        assert values[0] == x
        assert values[1].value == '1'
        assert values[2] == y
        assert values[3].value == '2'

    def test_values_complex_nesting(self):
        """Test values extraction from complex nested structure."""
        # Build: (p(x, y) ∧ q(z)) → r(x)
        x = Variable(name='x')
        y = Variable(name='y')
        z = Variable(name='z')

        p = Predicate(name='p', args=[x, y])
        q = Predicate(name='q', args=[z])
        r = Predicate(name='r', args=[x])

        and_part = And(left=p, right=q)
        implies = Implies(antecedent=and_part, consequent=r)

        values = list(implies.values())
        # Should get x, y from p, then z from q, then x from r
        assert len(values) == 4
        assert values[0] == x
        assert values[1] == y
        assert values[2] == z
        assert values[3] == x  # x appears twice


class TestFormulaNormalization:
    """Test normalization of formulas to basis operators."""

    def test_normalize_or(self):
        """Test normalization of Or formula."""
        left = Bool(value=True)
        right = Bool(value=False)
        or_formula = Or(left=left, right=right)

        normalized = normalize_root_formula(or_formula)

        # Should be: ¬(¬left ∧ ¬right)
        assert isinstance(normalized, Not)
        assert isinstance(normalized.operand, And)
        assert isinstance(normalized.operand.left, Not)
        assert isinstance(normalized.operand.right, Not)
        assert normalized.operand.left.operand == left
        assert normalized.operand.right.operand == right

    def test_normalize_implies(self):
        """Test normalization of Implies formula."""
        antecedent = Bool(value=True)
        consequent = Bool(value=False)
        implies = Implies(antecedent=antecedent, consequent=consequent)

        normalized = normalize_root_formula(implies)

        # Should be: ¬(antecedent ∧ ¬consequent)
        assert isinstance(normalized, Not)
        assert isinstance(normalized.operand, And)
        assert normalized.operand.left == antecedent
        assert isinstance(normalized.operand.right, Not)
        assert normalized.operand.right.operand == consequent

    def test_normalize_future(self):
        """Test normalization of Future formula."""
        operand = Predicate(name='p')
        future = Future(operand=operand)

        normalized = normalize_root_formula(future)

        # Should be: true U operand
        assert isinstance(normalized, Until)
        assert isinstance(normalized.left, Bool)
        assert normalized.left.value is True
        assert normalized.right == operand

    def test_normalize_preserves_basis_operators(self):
        """Test that basis operators are not modified."""
        formulas = [
            Bool(value=True),
            Not(operand=Bool(value=False)),
            And(left=Bool(value=True), right=Bool(value=False)),
            Next(operand=Predicate(name='p')),
            Until(left=Predicate(name='p'), right=Predicate(name='q')),
            Global(operand=Predicate(name='p')),
        ]

        for formula in formulas:
            normalized = normalize_root_formula(formula)
            assert normalized == formula

    def test_normalize_non_temporal_formulas(self):
        """Test normalization doesn't affect non-temporal formulas in basis."""
        formulas = [
            Equal(left=Variable(name='x'), right=Atom(value='42')),
            Predicate(name='p', args=[Variable(name='x')]),
        ]

        for formula in formulas:
            normalized = normalize_root_formula(formula)
            assert normalized == formula

    def test_normalize_complex_formula(self):
        """Test normalization of complex nested formula."""
        # Build: (p ∨ q) → F(r)
        p = Predicate(name='p')
        q = Predicate(name='q')
        r = Predicate(name='r')

        or_part = Or(left=p, right=q)
        future_part = Future(operand=r)
        implies = Implies(antecedent=or_part, consequent=future_part)

        # Only normalize the root
        normalized = normalize_root_formula(implies)

        # Should be: ¬((p ∨ q) ∧ ¬F(r))
        assert isinstance(normalized, Not)
        assert isinstance(normalized.operand, And)
        assert normalized.operand.left == or_part  # Or not normalized (only root)
        assert isinstance(normalized.operand.right, Not)
        assert normalized.operand.right.operand == future_part

    def test_normalize_does_not_recurse(self):
        """Test that normalize_root_formula only normalizes the root."""
        # Build: G(p ∨ q)
        p = Predicate(name='p')
        q = Predicate(name='q')
        or_part = Or(left=p, right=q)
        global_formula = Global(operand=or_part)

        normalized = normalize_root_formula(global_formula)

        # Global is in basis, so it shouldn't change
        # The inner Or should also not be normalized
        assert normalized == global_formula
        assert isinstance(normalized.operand, Or)


class TestFormulaStringRepresentation:
    """Test string representations of formulas."""

    def test_value_str(self):
        """Test string representation of values."""
        var = Variable(name='x')
        assert str(var) == 'x'

        atom = Atom(value='hello')
        assert str(atom) == 'hello'

    def test_equal_str(self):
        """Test string representation of Equal."""
        eq = Equal(left=Variable(name='x'), right=Atom(value='42'))
        assert str(eq) == 'x = 42'

    def test_bool_str(self):
        """Test string representation of Bool."""
        assert str(Bool(value=True)) == 'true'
        assert str(Bool(value=False)) == 'false'

    def test_predicate_str(self):
        """Test string representation of Predicate."""
        # No args
        p1 = Predicate(name='p')
        assert str(p1) == 'p'

        # With args
        p2 = Predicate(name='foo', args=[Variable(name='x'), Atom(value='42')])
        assert str(p2) == 'foo(x, 42)'

    def test_complex_formula_str(self):
        """Test string representation of complex formulas."""
        # Build: G(p → F(q))
        p = Predicate(name='p')
        q = Predicate(name='q')
        f_q = Future(operand=q)
        implies = Implies(antecedent=p, consequent=f_q)
        global_formula = Global(operand=implies)

        assert str(global_formula) == 'G(p → Fq)'


class TestPredicateProperties:
    """Test Predicate-specific properties."""

    def test_is_atomic(self):
        """Test is_atomic property of Predicate."""
        # Atomic predicate (no args)
        p1 = Predicate(name='p')
        assert p1.is_atomic is True

        # Non-atomic predicate (with args)
        p2 = Predicate(name='p', args=[Variable(name='x')])
        assert p2.is_atomic is False

        p3 = Predicate(name='foo', args=[Variable(name='x'), Variable(name='y')])
        assert p3.is_atomic is False


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_predicate_args(self):
        """Test Predicate with explicitly empty args list."""
        p = Predicate(name='p', args=[])
        assert p.is_atomic is True
        assert list(p.values()) == []
        assert str(p) == 'p'

    def test_deeply_nested_normalization(self):
        """Test normalization preserves structure for non-root operators."""
        # Build: Not(Or(Future(p), Implies(q, r)))
        p = Predicate(name='p')
        q = Predicate(name='q')
        r = Predicate(name='r')

        future_p = Future(operand=p)
        implies_qr = Implies(antecedent=q, consequent=r)
        or_formula = Or(left=future_p, right=implies_qr)
        not_formula = Not(operand=or_formula)

        # Normalize the Not (which is already in basis)
        normalized = normalize_root_formula(not_formula)

        # Should be unchanged since Not is in basis
        assert normalized == not_formula
        # Inner formulas should not be normalized
        assert isinstance(normalized.operand, Or)
        assert isinstance(normalized.operand.left, Future)
        assert isinstance(normalized.operand.right, Implies)

    def test_multiple_value_occurrences(self):
        """Test that values() correctly returns all occurrences."""
        x = Variable(name='x')
        # Build: (x = 1) ∧ (x = 2)
        eq1 = Equal(left=x, right=Atom(value='1'))
        eq2 = Equal(left=x, right=Atom(value='2'))
        and_formula = And(left=eq1, right=eq2)

        values = list(and_formula.values())
        assert len(values) == 4
        # x appears twice
        x_occurrences = [v for v in values if isinstance(v, Variable) and v.name == 'x']
        assert len(x_occurrences) == 2
