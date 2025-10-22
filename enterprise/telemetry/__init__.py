"""OpenHands Enterprise Telemetry Collection Framework.

This package provides a pluggable metrics collection framework that allows
developers to easily define and register custom metrics collectors for the
OpenHands Enterprise Telemetry Service.
"""

from .base_collector import MetricResult, MetricsCollector
from .registry import CollectorRegistry, register_collector, collector_registry

__all__ = [
    'MetricResult',
    'MetricsCollector', 
    'CollectorRegistry',
    'register_collector',
    'collector_registry'
]