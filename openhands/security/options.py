from openhands.security.analyzer import SecurityAnalyzer
from openhands.security.grayswan.analyzer import GraySwanAnalyzer
from openhands.security.invariant.analyzer import InvariantAnalyzer
from openhands.security.llm.analyzer import LLMRiskAnalyzer

SecurityAnalyzers: dict[str, type[SecurityAnalyzer]] = {
    'invariant': InvariantAnalyzer,
    'llm': LLMRiskAnalyzer,
    'grayswan': GraySwanAnalyzer,
}
