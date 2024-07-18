from opendevin.security.analyzer import SecurityAnalyzer
from opendevin.security.invariant.analyzer import InvariantAnalyzer
from typing import Dict

SecurityAnalyzers: Dict[str, SecurityAnalyzer] = {
    'invariant': InvariantAnalyzer,
}
