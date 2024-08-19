if __package__ is None or __package__ == '':
    from linter import Linter, LintResult
else:
    from .linter import Linter, LintResult

__all__ = ['Linter', 'LintResult']
