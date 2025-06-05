"""
LTL (Linear Temporal Logic) specification definitions and checker.

This module defines the format for LTL specifications and provides
a checker to validate event histories against these specifications.
"""

import re
from dataclasses import dataclass
from typing import List, Set, Dict, Any, Optional, Union
from enum import Enum


class LTLOperator(str, Enum):
    """LTL temporal operators."""
    NEXT = 'X'          # Next (in the next state)
    FINALLY = 'F'       # Finally (eventually)
    GLOBALLY = 'G'      # Globally (always)
    UNTIL = 'U'         # Until
    RELEASE = 'R'       # Release
    
    # Logical operators
    AND = '&'           # Logical AND
    OR = '|'            # Logical OR  
    NOT = '!'           # Logical NOT
    IMPLIES = '->'      # Logical implication


@dataclass
class LTLSpecification:
    """
    An LTL specification for security analysis.
    
    Examples:
    - "Never write to a file without reading it first":
      G(action_file_write -> (F[past](action_file_read & same_file)))
      
    - "Never browse the same URL twice without an action in between":
      G(action_browse_url -> X(G(action_browse_url & same_url -> F(action_non_browse))))
      
    - "Always require confirmation for high-risk actions":
      G(state_high_risk -> confirmation_required)
    """
    
    name: str
    description: str
    formula: str
    severity: str = 'MEDIUM'  # LOW, MEDIUM, HIGH
    enabled: bool = True
    
    def __post_init__(self):
        """Validate the specification after creation."""
        if self.severity not in ['LOW', 'MEDIUM', 'HIGH']:
            raise ValueError(f"Invalid severity: {self.severity}")


class LTLFormulaParser:
    """Parser for LTL formulas with simplified syntax."""
    
    def __init__(self):
        # Simplified operators for easier specification writing
        self.operators = {
            'G': 'G',      # Globally (always)
            'F': 'F',      # Finally (eventually)  
            'X': 'X',      # Next
            'U': 'U',      # Until
            '!': '!',      # Not
            '&': '&',      # And
            '|': '|',      # Or
            '->': '->',    # Implies
            '()': '()',    # Parentheses
        }
    
    def parse(self, formula: str) -> 'ParsedLTLFormula':
        """
        Parse an LTL formula into a structured representation.
        
        This is a simplified parser for demonstration purposes.
        A full implementation would use a proper grammar and AST.
        """
        # TODO: Implement proper LTL formula parsing
        return ParsedLTLFormula(formula, self._tokenize(formula))
    
    def _tokenize(self, formula: str) -> List[str]:
        """Tokenize the formula into operators and predicates."""
        # Simple tokenization - a real parser would be more sophisticated
        tokens = []
        current_token = ""
        
        i = 0
        while i < len(formula):
            char = formula[i]
            
            if char.isspace():
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            elif char in '()!&|':
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                tokens.append(char)
            elif char == '-' and i + 1 < len(formula) and formula[i + 1] == '>':
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                tokens.append('->')
                i += 1  # Skip the '>'
            else:
                current_token += char
            
            i += 1
        
        if current_token:
            tokens.append(current_token)
            
        return tokens


@dataclass
class ParsedLTLFormula:
    """A parsed LTL formula."""
    original: str
    tokens: List[str]


class LTLChecker:
    """
    Checker for LTL specifications against predicate histories.
    
    This is a simplified implementation for demonstration purposes.
    A production implementation would use a proper LTL model checker.
    """
    
    def __init__(self):
        self.parser = LTLFormulaParser()
    
    def check_specification(
        self, 
        spec: LTLSpecification, 
        predicate_history: List[Set[str]]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a specification is violated by the current predicate history.
        
        Args:
            spec: The LTL specification to check
            predicate_history: History of predicate sets from events
            
        Returns:
            None if no violation, violation details dict if violated
        """
        if not spec.enabled or not predicate_history:
            return None
            
        try:
            parsed_formula = self.parser.parse(spec.formula)
            return self._evaluate_formula(parsed_formula, predicate_history, spec)
        except Exception as e:
            return {
                'error': f'Failed to evaluate formula: {e}',
                'severity': spec.severity,
                'timestamp': None
            }
    
    def _evaluate_formula(
        self, 
        formula: ParsedLTLFormula, 
        history: List[Set[str]], 
        spec: LTLSpecification
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate a parsed LTL formula against the predicate history.
        
        This is a simplified implementation that handles some common patterns.
        """
        # Simple pattern matching for demonstration
        original = formula.original.strip()
        
        # Pattern: G(p -> q) - "globally, if p then q"
        if self._matches_global_implication(original):
            return self._check_global_implication(original, history, spec)
            
        # Pattern: G(!p) - "globally not p" 
        if self._matches_global_negation(original):
            return self._check_global_negation(original, history, spec)
            
        # Pattern: F(p) - "eventually p"
        if self._matches_eventually(original):
            return self._check_eventually(original, history, spec)
            
        # Default: no violation detected (or formula not supported)
        return None
    
    def _matches_global_implication(self, formula: str) -> bool:
        """Check if formula matches G(p -> q) pattern."""
        return re.match(r'G\s*\(\s*.+\s*->\s*.+\s*\)', formula) is not None
    
    def _matches_global_negation(self, formula: str) -> bool:
        """Check if formula matches G(!p) pattern."""
        return re.match(r'G\s*\(\s*!\s*.+\s*\)', formula) is not None
    
    def _matches_eventually(self, formula: str) -> bool:
        """Check if formula matches F(p) pattern."""
        return re.match(r'F\s*\(\s*.+\s*\)', formula) is not None
    
    def _check_global_implication(
        self, 
        formula: str, 
        history: List[Set[str]], 
        spec: LTLSpecification
    ) -> Optional[Dict[str, Any]]:
        """Check G(p -> q) - if p occurs, q must also occur."""
        # Extract p and q from G(p -> q)
        match = re.match(r'G\s*\(\s*(.+?)\s*->\s*(.+?)\s*\)', formula)
        if not match:
            return None
            
        antecedent = match.group(1).strip()
        consequent = match.group(2).strip()
        
        # Check each state in history
        for i, predicates in enumerate(history):
            if self._predicate_matches(antecedent, predicates):
                # p is true, check if q is also true
                if not self._predicate_matches(consequent, predicates):
                    return {
                        'type': 'global_implication_violation',
                        'antecedent': antecedent,
                        'consequent': consequent,
                        'violation_step': i,
                        'predicates_at_violation': list(predicates),
                        'severity': spec.severity,
                        'message': f'Antecedent "{antecedent}" was true but consequent "{consequent}" was false'
                    }
        
        return None
    
    def _check_global_negation(
        self, 
        formula: str, 
        history: List[Set[str]], 
        spec: LTLSpecification
    ) -> Optional[Dict[str, Any]]:
        """Check G(!p) - p should never occur."""
        # Extract p from G(!p)
        match = re.match(r'G\s*\(\s*!\s*(.+?)\s*\)', formula)
        if not match:
            return None
            
        predicate = match.group(1).strip()
        
        # Check each state in history
        for i, predicates in enumerate(history):
            if self._predicate_matches(predicate, predicates):
                return {
                    'type': 'global_negation_violation',
                    'forbidden_predicate': predicate,
                    'violation_step': i,
                    'predicates_at_violation': list(predicates),
                    'severity': spec.severity,
                    'message': f'Forbidden predicate "{predicate}" occurred'
                }
        
        return None
    
    def _check_eventually(
        self, 
        formula: str, 
        history: List[Set[str]], 
        spec: LTLSpecification
    ) -> Optional[Dict[str, Any]]:
        """Check F(p) - p should eventually occur."""
        # Extract p from F(p)
        match = re.match(r'F\s*\(\s*(.+?)\s*\)', formula)
        if not match:
            return None
            
        predicate = match.group(1).strip()
        
        # Check if predicate ever occurs in history
        for predicates in history:
            if self._predicate_matches(predicate, predicates):
                return None  # Found it, no violation
        
        # If we reach here and history is substantial, it's a violation
        if len(history) > 10:  # Arbitrary threshold
            return {
                'type': 'eventually_violation',
                'required_predicate': predicate,
                'history_length': len(history),
                'severity': spec.severity,
                'message': f'Required predicate "{predicate}" never occurred'
            }
        
        return None
    
    def _predicate_matches(self, predicate_expr: str, predicates: Set[str]) -> bool:
        """
        Check if a predicate expression matches the current predicates.
        
        Supports simple expressions like:
        - "p" - predicate p is present
        - "p & q" - both p and q are present
        - "p | q" - either p or q is present
        """
        expr = predicate_expr.strip()
        
        # Simple predicate
        if ' ' not in expr and expr in predicates:
            return True
            
        # Handle & (AND)
        if ' & ' in expr:
            parts = [p.strip() for p in expr.split(' & ')]
            return all(part in predicates for part in parts)
            
        # Handle | (OR)
        if ' | ' in expr:
            parts = [p.strip() for p in expr.split(' | ')]
            return any(part in predicates for part in parts)
        
        # Default: exact match
        return expr in predicates


def create_default_ltl_specifications() -> List[LTLSpecification]:
    """Create a set of default LTL specifications for common security patterns."""
    return [
        LTLSpecification(
            name="no_write_without_read",
            description="Never write to a file without reading it first in the same session",
            formula="G(action_file_write -> F_past(action_file_read))",
            severity="MEDIUM"
        ),
        
        LTLSpecification(
            name="no_repeated_browsing",
            description="Never browse the same URL twice without a non-browse action in between",
            formula="G(action_browse_url -> X(G(action_browse_url -> action_non_browse)))",
            severity="LOW"
        ),
        
        LTLSpecification(
            name="no_sensitive_file_access",
            description="Never access sensitive files",
            formula="G(!action_file_read_sensitive_file & !action_file_write_sensitive_file)",
            severity="HIGH"
        ),
        
        LTLSpecification(
            name="no_risky_commands",
            description="Never execute risky commands without confirmation",
            formula="G(action_cmd_risky -> confirmation_required)",
            severity="HIGH"
        ),
        
        LTLSpecification(
            name="error_recovery",
            description="After an error, agent should not continue with high-risk actions",
            formula="G(state_error_occurred -> X(G(!state_high_risk)))",
            severity="MEDIUM"
        ),
        
        LTLSpecification(
            name="no_external_network_access",
            description="Never access external URLs without explicit permission",
            formula="G(!action_browse_external_url)",
            severity="MEDIUM"
        ),
        
        LTLSpecification(
            name="command_success_check",
            description="After running a command, check if it succeeded",
            formula="G(action_cmd_run -> X(F(obs_cmd_success | obs_cmd_error)))",
            severity="LOW"
        ),
        
        LTLSpecification(
            name="no_package_installation",
            description="Never install packages without permission",
            formula="G(!action_cmd_package_install)",
            severity="HIGH"
        )
    ]


# TODO: Add more sophisticated LTL patterns
class AdvancedLTLPatterns:
    """
    More advanced LTL patterns that could be implemented.
    
    These are placeholders for future development.
    """
    
    @staticmethod
    def temporal_ordering():
        """Patterns for temporal ordering of events."""
        pass
    
    @staticmethod
    def state_invariants():
        """Patterns for maintaining state invariants."""
        pass
    
    @staticmethod
    def access_control():
        """Patterns for access control violations."""
        pass