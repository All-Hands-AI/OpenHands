# OpenHands Observability and Monitoring Guide

This guide covers comprehensive observability, monitoring, and metrics collection for OpenHands systems.

## Table of Contents
1. [Metrics Collection](#metrics-collection)
2. [Tracing System](#tracing-system)
3. [Monitoring Dashboard](#monitoring-dashboard)
4. [Alert System](#alert-system)

## Metrics Collection

### 1. Metrics Registry

Central system for collecting and managing metrics:

```python
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import json

@dataclass
class Metric:
    """Base metric class"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]
    type: str = "gauge"  # gauge, counter, histogram

class MetricsRegistry:
    """Central metrics registry"""
    
    def __init__(self):
        self.metrics: Dict[str, List[Metric]] = {}
        self.collectors = []
        self.running = False
        self._collection_task = None
        
    async def start(self):
        """Start metrics collection"""
        self.running = True
        self._collection_task = asyncio.create_task(
            self._collect_metrics()
        )
        
    async def stop(self):
        """Stop metrics collection"""
        self.running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
                
    def register_collector(self, collector: 'MetricsCollector'):
        """Register metrics collector"""
        self.collectors.append(collector)
        
    async def record_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Record a metric value"""
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {}
        )
        
        if name not in self.metrics:
            self.metrics[name] = []
            
        self.metrics[name].append(metric)
        
        # Trim old metrics
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-1000:]
            
    async def get_metrics(
        self,
        name: Optional[str] = None
    ) -> Dict[str, List[Metric]]:
        """Get recorded metrics"""
        if name:
            return {name: self.metrics.get(name, [])}
        return self.metrics
        
    async def _collect_metrics(self):
        """Collect metrics from registered collectors"""
        while self.running:
            try:
                for collector in self.collectors:
                    metrics = await collector.collect()
                    for metric in metrics:
                        await self.record_metric(
                            metric.name,
                            metric.value,
                            metric.labels
                        )
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                
            await asyncio.sleep(60)  # Collect every minute
```

### 2. Metrics Collectors

Specialized metrics collectors:

```python
class MetricsCollector:
    """Base metrics collector"""
    
    async def collect(self) -> List[Metric]:
        """Collect metrics"""
        raise NotImplementedError

class SystemMetricsCollector(MetricsCollector):
    """System metrics collector"""
    
    async def collect(self) -> List[Metric]:
        """Collect system metrics"""
        metrics = []
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics.append(Metric(
            name="system_cpu_usage",
            value=cpu_percent,
            timestamp=datetime.now(),
            labels={"unit": "percent"}
        ))
        
        # Memory metrics
        memory = psutil.virtual_memory()
        metrics.append(Metric(
            name="system_memory_usage",
            value=memory.percent,
            timestamp=datetime.now(),
            labels={"unit": "percent"}
        ))
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        metrics.append(Metric(
            name="system_disk_usage",
            value=disk.percent,
            timestamp=datetime.now(),
            labels={"unit": "percent"}
        ))
        
        return metrics

class ApplicationMetricsCollector(MetricsCollector):
    """Application-specific metrics collector"""
    
    def __init__(self):
        self.counters = {
            "requests": 0,
            "errors": 0,
            "active_sessions": 0
        }
        
    async def collect(self) -> List[Metric]:
        """Collect application metrics"""
        metrics = []
        timestamp = datetime.now()
        
        for name, value in self.counters.items():
            metrics.append(Metric(
                name=f"app_{name}",
                value=value,
                timestamp=timestamp,
                labels={"type": "counter"},
                type="counter"
            ))
            
        return metrics
        
    def increment(self, metric: str, value: int = 1):
        """Increment counter metric"""
        if metric in self.counters:
            self.counters[metric] += value
```

## Tracing System

### 1. Distributed Tracing

Implementation of distributed tracing:

```python
from dataclasses import dataclass
from typing import Optional, List
import uuid
import time

@dataclass
class Span:
    """Tracing span"""
    id: str
    trace_id: str
    parent_id: Optional[str]
    name: str
    start_time: float
    end_time: Optional[float] = None
    tags: Dict[str, str] = None
    events: List[dict] = None

class TracingSystem:
    """Distributed tracing system"""
    
    def __init__(self):
        self.spans: Dict[str, Span] = {}
        self.active_spans: Dict[str, Span] = {}
        
    def start_span(
        self,
        name: str,
        parent_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> Span:
        """Start a new span"""
        span_id = str(uuid.uuid4())
        trace_id = trace_id or str(uuid.uuid4())
        
        span = Span(
            id=span_id,
            trace_id=trace_id,
            parent_id=parent_id,
            name=name,
            start_time=time.time(),
            tags={},
            events=[]
        )
        
        self.active_spans[span_id] = span
        return span
        
    def end_span(self, span: Span):
        """End a span"""
        span.end_time = time.time()
        self.spans[span.id] = span
        self.active_spans.pop(span.id, None)
        
    def add_tag(self, span: Span, key: str, value: str):
        """Add tag to span"""
        if not span.tags:
            span.tags = {}
        span.tags[key] = value
        
    def add_event(
        self,
        span: Span,
        name: str,
        attributes: Optional[Dict[str, str]] = None
    ):
        """Add event to span"""
        if not span.events:
            span.events = []
            
        span.events.append({
            'name': name,
            'timestamp': time.time(),
            'attributes': attributes or {}
        })
        
    def get_trace(self, trace_id: str) -> List[Span]:
        """Get all spans for a trace"""
        return [
            span for span in self.spans.values()
            if span.trace_id == trace_id
        ]

class TracingContext:
    """Context manager for tracing"""
    
    def __init__(
        self,
        tracer: TracingSystem,
        name: str,
        parent_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ):
        self.tracer = tracer
        self.name = name
        self.parent_id = parent_id
        self.trace_id = trace_id
        self.span = None
        
    async def __aenter__(self) -> Span:
        self.span = self.tracer.start_span(
            self.name,
            self.parent_id,
            self.trace_id
        )
        return self.span
        
    async def __aexit__(self, exc_type, exc, tb):
        if exc_type:
            self.tracer.add_tag(self.span, "error", "true")
            self.tracer.add_tag(
                self.span,
                "error.message",
                str(exc)
            )
        self.tracer.end_span(self.span)
```

## Monitoring Dashboard

### 1. Dashboard System

Implementation of monitoring dashboard:

```python
class DashboardMetrics:
    """Dashboard metrics collector and formatter"""
    
    def __init__(
        self,
        metrics_registry: MetricsRegistry,
        tracing_system: TracingSystem
    ):
        self.metrics_registry = metrics_registry
        self.tracing_system = tracing_system
        
    async def get_system_metrics(self) -> dict:
        """Get system metrics for dashboard"""
        metrics = await self.metrics_registry.get_metrics()
        
        return {
            'cpu': self._format_metric(
                metrics.get('system_cpu_usage', [])
            ),
            'memory': self._format_metric(
                metrics.get('system_memory_usage', [])
            ),
            'disk': self._format_metric(
                metrics.get('system_disk_usage', [])
            )
        }
        
    async def get_application_metrics(self) -> dict:
        """Get application metrics for dashboard"""
        metrics = await self.metrics_registry.get_metrics()
        
        return {
            'requests': self._format_metric(
                metrics.get('app_requests', [])
            ),
            'errors': self._format_metric(
                metrics.get('app_errors', [])
            ),
            'sessions': self._format_metric(
                metrics.get('app_active_sessions', [])
            )
        }
        
    async def get_trace_metrics(self) -> dict:
        """Get tracing metrics for dashboard"""
        spans = list(self.tracing_system.spans.values())
        
        return {
            'total_traces': len(set(s.trace_id for s in spans)),
            'total_spans': len(spans),
            'error_spans': len([
                s for s in spans
                if s.tags and s.tags.get('error') == 'true'
            ]),
            'avg_duration': sum(
                (s.end_time - s.start_time)
                for s in spans if s.end_time
            ) / len(spans) if spans else 0
        }
        
    def _format_metric(self, metrics: List[Metric]) -> dict:
        """Format metrics for dashboard"""
        if not metrics:
            return {
                'current': 0,
                'min': 0,
                'max': 0,
                'avg': 0
            }
            
        values = [m.value for m in metrics]
        return {
            'current': values[-1],
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values)
        }
```

## Alert System

### 1. Alert Manager

Implementation of alert management system:

```python
from enum import Enum
from typing import Optional, List, Callable

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    """Alert definition"""
    id: str
    name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    context: Optional[dict] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class AlertManager:
    """Alert management system"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.handlers: Dict[AlertSeverity, List[Callable]] = {
            severity: [] for severity in AlertSeverity
        }
        
    async def create_alert(
        self,
        name: str,
        severity: AlertSeverity,
        message: str,
        context: Optional[dict] = None
    ) -> Alert:
        """Create new alert"""
        alert = Alert(
            id=str(uuid.uuid4()),
            name=name,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            context=context
        )
        
        self.alerts[alert.id] = alert
        
        # Handle alert
        await self._handle_alert(alert)
        
        return alert
        
    async def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
    def register_handler(
        self,
        severity: AlertSeverity,
        handler: Callable
    ):
        """Register alert handler"""
        self.handlers[severity].append(handler)
        
    async def _handle_alert(self, alert: Alert):
        """Handle alert with registered handlers"""
        for handler in self.handlers[alert.severity]:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(
                    f"Alert handler error: {e}"
                )

class AlertRule:
    """Alert rule definition"""
    
    def __init__(
        self,
        name: str,
        severity: AlertSeverity,
        condition: Callable,
        message_template: str
    ):
        self.name = name
        self.severity = severity
        self.condition = condition
        self.message_template = message_template
        
    async def evaluate(
        self,
        context: dict
    ) -> Optional[dict]:
        """Evaluate alert rule"""
        try:
            if await self.condition(context):
                return {
                    'name': self.name,
                    'severity': self.severity,
                    'message': self.message_template.format(
                        **context
                    ),
                    'context': context
                }
        except Exception as e:
            logger.error(
                f"Alert rule evaluation error: {e}"
            )
        return None

class AlertEvaluator:
    """Alert rules evaluator"""
    
    def __init__(
        self,
        alert_manager: AlertManager,
        metrics_registry: MetricsRegistry
    ):
        self.alert_manager = alert_manager
        self.metrics_registry = metrics_registry
        self.rules: List[AlertRule] = []
        
    def add_rule(self, rule: AlertRule):
        """Add alert rule"""
        self.rules.append(rule)
        
    async def evaluate_rules(self):
        """Evaluate all alert rules"""
        metrics = await self.metrics_registry.get_metrics()
        context = {
            'metrics': metrics,
            'timestamp': datetime.now()
        }
        
        for rule in self.rules:
            result = await rule.evaluate(context)
            if result:
                await self.alert_manager.create_alert(
                    name=result['name'],
                    severity=result['severity'],
                    message=result['message'],
                    context=result['context']
                )
```

Remember to:
- Configure appropriate metrics collection
- Set up comprehensive tracing
- Implement proper alerting
- Monitor system health
- Analyze performance trends
- Document monitoring procedures
- Maintain observability systems