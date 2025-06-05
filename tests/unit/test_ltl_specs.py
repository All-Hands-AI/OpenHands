"""Unit tests for LTL specifications and checker.

Tests the LTL specification parsing, validation, and checking functionality.
"""

import pytest

from openhands.security.ltl.specs import (
    LTLChecker,
    LTLFormulaParser,
    LTLSpecification,
    ParsedLTLFormula,
    create_default_ltl_specifications,
)


class TestLTLSpecification:
    """Test the LTLSpecification dataclass."""

    def test_ltl_specification_creation(self):
        """Test creating a valid LTL specification."""
        spec = LTLSpecification(
            name='test_spec',
            description='A test specification',
            formula='G(p -> q)',
            severity='HIGH',
        )

        assert spec.name == 'test_spec'
        assert spec.description == 'A test specification'
        assert spec.formula == 'G(p -> q)'
        assert spec.severity == 'HIGH'
        assert spec.enabled is True  # Default value

    def test_ltl_specification_invalid_severity(self):
        """Test that invalid severity raises ValueError."""
        with pytest.raises(ValueError, match='Invalid severity'):
            LTLSpecification(
                name='test_spec',
                description='A test specification',
                formula='G(p -> q)',
                severity='INVALID',
            )

    def test_ltl_specification_defaults(self):
        """Test default values for LTL specification."""
        spec = LTLSpecification(
            name='test_spec', description='A test specification', formula='G(p -> q)'
        )

        assert spec.severity == 'MEDIUM'
        assert spec.enabled is True


class TestLTLFormulaParser:
    """Test the LTL formula parser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = LTLFormulaParser()

    def test_parser_init(self):
        """Test parser initialization."""
        assert self.parser is not None
        assert 'G' in self.parser.operators
        assert 'F' in self.parser.operators
        assert '->' in self.parser.operators

    def test_tokenize_simple_formula(self):
        """Test tokenizing a simple formula."""
        tokens = self.parser._tokenize('G(p -> q)')

        assert 'G' in tokens
        assert '(' in tokens
        assert 'p' in tokens
        assert '->' in tokens
        assert 'q' in tokens
        assert ')' in tokens

    def test_tokenize_complex_formula(self):
        """Test tokenizing a more complex formula."""
        tokens = self.parser._tokenize('G(p & q | !r)')

        assert 'G' in tokens
        assert 'p' in tokens
        assert '&' in tokens
        assert 'q' in tokens
        assert '|' in tokens
        assert '!' in tokens
        assert 'r' in tokens

    def test_tokenize_with_spaces(self):
        """Test tokenizing formula with various spacing."""
        tokens = self.parser._tokenize('G ( p  ->   q )')

        assert 'G' in tokens
        assert 'p' in tokens
        assert '->' in tokens
        assert 'q' in tokens
        # Spaces should be ignored

    def test_parse_returns_parsed_formula(self):
        """Test that parse returns a ParsedLTLFormula object."""
        formula = 'G(p -> q)'
        result = self.parser.parse(formula)

        assert isinstance(result, ParsedLTLFormula)
        assert result.original == formula
        assert len(result.tokens) > 0


class TestLTLChecker:
    """Test the LTL checker functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.checker = LTLChecker()

    def test_checker_init(self):
        """Test checker initialization."""
        assert self.checker is not None
        assert self.checker.parser is not None

    def test_check_specification_disabled(self):
        """Test that disabled specifications are skipped."""
        spec = LTLSpecification(
            name='test_spec',
            description='A test specification',
            formula='G(p -> q)',
            enabled=False,
        )

        result = self.checker.check_specification(spec, [])
        assert result is None

    def test_check_specification_empty_history(self):
        """Test that empty history returns no violation."""
        spec = LTLSpecification(
            name='test_spec', description='A test specification', formula='G(p -> q)'
        )

        result = self.checker.check_specification(spec, [])
        assert result is None

    def test_matches_global_implication(self):
        """Test pattern matching for global implication."""
        assert self.checker._matches_global_implication('G(p -> q)')
        assert self.checker._matches_global_implication('G( p -> q )')
        assert not self.checker._matches_global_implication('F(p -> q)')
        assert not self.checker._matches_global_implication('G(p & q)')

    def test_matches_global_negation(self):
        """Test pattern matching for global negation."""
        assert self.checker._matches_global_negation('G(!p)')
        assert self.checker._matches_global_negation('G( !p )')
        assert not self.checker._matches_global_negation('G(p)')
        assert not self.checker._matches_global_negation('F(!p)')

    def test_matches_eventually(self):
        """Test pattern matching for eventually."""
        assert self.checker._matches_eventually('F(p)')
        assert self.checker._matches_eventually('F( p )')
        assert not self.checker._matches_eventually('G(p)')
        assert not self.checker._matches_eventually('X(p)')

    def test_predicate_matches_simple(self):
        """Test simple predicate matching."""
        predicates = {'action_file_read', 'action_cmd_run', 'state_high_risk'}

        assert self.checker._predicate_matches('action_file_read', predicates)
        assert not self.checker._predicate_matches('action_file_write', predicates)

    def test_predicate_matches_and(self):
        """Test AND predicate matching."""
        predicates = {'action_file_read', 'action_cmd_run', 'state_high_risk'}

        assert self.checker._predicate_matches(
            'action_file_read & action_cmd_run', predicates
        )
        assert not self.checker._predicate_matches(
            'action_file_read & action_file_write', predicates
        )

    def test_predicate_matches_or(self):
        """Test OR predicate matching."""
        predicates = {'action_file_read', 'action_cmd_run', 'state_high_risk'}

        assert self.checker._predicate_matches(
            'action_file_read | action_file_write', predicates
        )
        assert (
            self.checker._predicate_matches(
                'action_file_write | action_browse_url', predicates
            )
            is False
        )

    def test_check_global_implication_no_violation(self):
        """Test global implication with no violation."""
        spec = LTLSpecification(
            name='test_spec',
            description='Test spec',
            formula='G(action_file_read -> obs_file_read_success)',
        )

        # History where whenever action_file_read occurs, obs_file_read_success also occurs
        history = [
            {'action_file_read', 'obs_file_read_success'},
            {'action_cmd_run'},
            {'action_file_read', 'obs_file_read_success', 'other_predicate'},
        ]

        result = self.checker.check_specification(spec, history)
        assert result is None

    def test_check_global_implication_violation(self):
        """Test global implication with violation."""
        spec = LTLSpecification(
            name='test_spec',
            description='Test spec',
            formula='G(action_file_read -> obs_file_read_success)',
            severity='HIGH',
        )

        # History where action_file_read occurs without obs_file_read_success
        history = [
            {'action_file_read'},  # Violation: antecedent true, consequent false
            {'action_cmd_run'},
        ]

        result = self.checker.check_specification(spec, history)
        assert result is not None
        assert result['type'] == 'global_implication_violation'
        assert result['antecedent'] == 'action_file_read'
        assert result['consequent'] == 'obs_file_read_success'
        assert result['violation_step'] == 0
        assert result['severity'] == 'HIGH'

    def test_check_global_negation_no_violation(self):
        """Test global negation with no violation."""
        spec = LTLSpecification(
            name='test_spec',
            description='Test spec',
            formula='G(!action_file_write_sensitive_file)',
        )

        # History without the forbidden predicate
        history = [
            {'action_file_read'},
            {'action_cmd_run'},
            {'action_file_write'},  # Regular file write, not sensitive
        ]

        result = self.checker.check_specification(spec, history)
        assert result is None

    def test_check_global_negation_violation(self):
        """Test global negation with violation."""
        spec = LTLSpecification(
            name='test_spec',
            description='Test spec',
            formula='G(!action_file_write_sensitive_file)',
            severity='HIGH',
        )

        # History with the forbidden predicate
        history = [
            {'action_file_read'},
            {'action_file_write_sensitive_file'},  # Violation: forbidden predicate
            {'action_cmd_run'},
        ]

        result = self.checker.check_specification(spec, history)
        assert result is not None
        assert result['type'] == 'global_negation_violation'
        assert result['forbidden_predicate'] == 'action_file_write_sensitive_file'
        assert result['violation_step'] == 1
        assert result['severity'] == 'HIGH'

    def test_check_eventually_no_violation(self):
        """Test eventually with no violation (predicate found)."""
        spec = LTLSpecification(
            name='test_spec', description='Test spec', formula='F(obs_cmd_success)'
        )

        # History where the required predicate eventually occurs
        history = [
            {'action_cmd_run'},
            {'action_file_read'},
            {'obs_cmd_success'},  # Required predicate found
        ]

        result = self.checker.check_specification(spec, history)
        assert result is None

    def test_check_eventually_violation_long_history(self):
        """Test eventually with violation (predicate never found in long history)."""
        spec = LTLSpecification(
            name='test_spec',
            description='Test spec',
            formula='F(obs_cmd_success)',
            severity='MEDIUM',
        )

        # Long history without the required predicate
        history = [{'action_cmd_run'} for _ in range(15)]  # 15 > 10 threshold

        result = self.checker.check_specification(spec, history)
        assert result is not None
        assert result['type'] == 'eventually_violation'
        assert result['required_predicate'] == 'obs_cmd_success'
        assert result['history_length'] == 15
        assert result['severity'] == 'MEDIUM'

    def test_check_eventually_no_violation_short_history(self):
        """Test eventually with short history (no violation yet)."""
        spec = LTLSpecification(
            name='test_spec', description='Test spec', formula='F(obs_cmd_success)'
        )

        # Short history without the required predicate (not a violation yet)
        history = [{'action_cmd_run'} for _ in range(5)]  # 5 <= 10 threshold

        result = self.checker.check_specification(spec, history)
        assert result is None

    def test_check_specification_invalid_formula(self):
        """Test handling of invalid formulas."""
        spec = LTLSpecification(
            name='test_spec',
            description='Test spec',
            formula='INVALID_FORMULA()',
            severity='LOW',
        )

        history = [{'some_predicate'}]

        # Should not crash, might return error or None
        result = self.checker.check_specification(spec, history)
        # Result could be None (unsupported pattern) or an error dict
        if result is not None:
            # If an error is returned, it should contain error info
            assert 'error' in result or result is None


class TestDefaultLTLSpecifications:
    """Test the default LTL specifications."""

    def test_create_default_ltl_specifications(self):
        """Test creating default LTL specifications."""
        specs = create_default_ltl_specifications()

        assert len(specs) > 0
        assert all(isinstance(spec, LTLSpecification) for spec in specs)

        # Check some expected specifications exist
        spec_names = [spec.name for spec in specs]
        assert 'no_sensitive_file_access' in spec_names
        assert 'no_risky_commands' in spec_names
        assert 'no_package_installation' in spec_names

    def test_default_specifications_are_valid(self):
        """Test that all default specifications are valid."""
        specs = create_default_ltl_specifications()

        for spec in specs:
            assert spec.name
            assert spec.description
            assert spec.formula
            assert spec.severity in ['LOW', 'MEDIUM', 'HIGH']
            assert isinstance(spec.enabled, bool)

    def test_default_specifications_high_severity(self):
        """Test that some default specifications have high severity."""
        specs = create_default_ltl_specifications()
        high_severity_specs = [spec for spec in specs if spec.severity == 'HIGH']

        assert len(high_severity_specs) > 0

        # Check specific high-severity specs
        high_severity_names = [spec.name for spec in high_severity_specs]
        assert 'no_sensitive_file_access' in high_severity_names
        assert 'no_risky_commands' in high_severity_names


# These tests will likely fail due to unimplemented or incomplete features


class TestLTLCheckerAdvancedPatterns:
    """Tests for advanced LTL patterns that may not be implemented yet."""

    def setup_method(self):
        """Set up test fixtures."""
        self.checker = LTLChecker()

    def test_unsupported_pattern_until(self):
        """Test handling of UNTIL patterns (likely unimplemented)."""
        spec = LTLSpecification(
            name='test_until',
            description='Test until pattern',
            formula='action_file_read U obs_file_read_success',
        )

        history = [{'action_file_read'}, {'obs_file_read_success'}]

        # This will likely return None since UNTIL patterns aren't implemented
        result = self.checker.check_specification(spec, history)
        assert result is None  # Expected since pattern not supported

    def test_unsupported_pattern_next(self):
        """Test handling of NEXT patterns (likely unimplemented)."""
        spec = LTLSpecification(
            name='test_next',
            description='Test next pattern',
            formula='X(obs_cmd_success)',
        )

        history = [{'action_cmd_run'}, {'obs_cmd_success'}]

        # This will likely return None since NEXT patterns aren't implemented
        result = self.checker.check_specification(spec, history)
        assert result is None  # Expected since pattern not supported

    def test_complex_nested_formula(self):
        """Test handling of complex nested formulas (likely unsupported)."""
        spec = LTLSpecification(
            name='test_complex',
            description='Test complex pattern',
            formula='G((action_file_read & action_file_write) -> F(obs_file_success))',
        )

        history = [{'action_file_read', 'action_file_write'}, {'obs_file_success'}]

        # Complex patterns likely not fully supported
        self.checker.check_specification(spec, history)
        # May return None or partial results
