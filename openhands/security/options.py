from openhands.security.analyzer import SecurityAnalyzer
from openhands.security.command_approval.analyzer import CommandApprovalAnalyzer
from openhands.security.invariant.analyzer import InvariantAnalyzer

SecurityAnalyzers: dict[str, type[SecurityAnalyzer]] = {
    'invariant': InvariantAnalyzer,
    'command_approval': CommandApprovalAnalyzer,
}
