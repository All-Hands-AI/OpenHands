from typing import Type

from openhands.security.analyzer import SecurityAnalyzer
from openhands.security.invariant.analyzer import InvariantAnalyzer

SecurityAnalyzers: dict[str, Type[SecurityAnalyzer]] = {
    'invariant': InvariantAnalyzer,
}
