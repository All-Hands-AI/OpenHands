from openhands.security.analyzer import SecurityAnalyzer
from openhands.security.invariant.analyzer import InvariantAnalyzer

SecurityAnalyzers: dict[str, type[SecurityAnalyzer]] = {
    'invariant': InvariantAnalyzer,
}
