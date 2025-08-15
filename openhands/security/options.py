from openhands.security.analyzer import SecurityAnalyzer
from openhands.security.invariant.analyzer import InvariantAnalyzer
from openhands.security.llm.analyzer import LLMRiskAnalyzer
from openhands.security.none.analyzer import NoneAnalyzer

SecurityAnalyzers: dict[str, type[SecurityAnalyzer]] = {
    'llm': LLMRiskAnalyzer,
    'invariant': InvariantAnalyzer,
    'none': NoneAnalyzer,
}
