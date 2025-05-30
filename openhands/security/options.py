from openhands.security.analyzer import SecurityAnalyzer
from openhands.security.bully import BullySecurityAnalyzer
from openhands.security.invariant.analyzer import InvariantAnalyzer
from openhands.security.llm_analyzer import LLMSecurityAnalyzer
from openhands.security.pushover import PushoverSecurityAnalyzer

SecurityAnalyzers: dict[str, type[SecurityAnalyzer]] = {
    'invariant': InvariantAnalyzer,
    'pushover': PushoverSecurityAnalyzer,
    'bully': BullySecurityAnalyzer,
    'llm': LLMSecurityAnalyzer,
}
