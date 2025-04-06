from typing import Dict, Type

from openhands.security.analyzer import SecurityAnalyzer
from openhands.security.invariant.analyzer import InvariantAnalyzer

SecurityAnalyzers: Dict[str, Type[SecurityAnalyzer]] = {
    'invariant': InvariantAnalyzer,
}
