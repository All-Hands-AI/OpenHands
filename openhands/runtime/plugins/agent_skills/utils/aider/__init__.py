if __package__ is None or __package__ == '':
    from linter import Linter, LintResult
else:
    from openhands.runtime.plugins.agent_skills.utils.aider.linter import (
        Linter,
        LintResult,
    )

__all__ = ['Linter', 'LintResult']
