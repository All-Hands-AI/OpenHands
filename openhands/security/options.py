from openhands.security.analyzer import SecurityAnalyzer
from openhands.security.invariant.analyzer import InvariantAnalyzer
from openhands.security.llm.analyzer import LLMRiskAnalyzer
from openhands.security.none.analyzer import NoneSecurityAnalyzer

SecurityAnalyzers: dict[str, type[SecurityAnalyzer]] = {
    'invariant': InvariantAnalyzer,
    'llm': LLMRiskAnalyzer,
    'none': NoneSecurityAnalyzer,
}
