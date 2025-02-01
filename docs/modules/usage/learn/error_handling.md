# OpenHands Error Handling Guide

This guide covers error handling patterns, recovery strategies, and fault tolerance mechanisms for OpenHands systems.

## Table of Contents
1. [Error Management](#error-management)
2. [Recovery Strategies](#recovery-strategies)
3. [Fault Tolerance](#fault-tolerance)
4. [Error Reporting](#error-reporting)

## Error Management

### 1. Error Handling System

Implementation of centralized error handling:

```python
from enum import Enum
from typing import Dict, List, Any, Optional, Type, Callable
import traceback
import asyncio
import logging

class ErrorSeverity(Enum):
    """Error severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories"""
    SYSTEM = "system"
    NETWORK = "network"
    DATABASE = "database"
    SECURITY = "security"
    BUSINESS = "business"
    VALIDATION = "validation"
    EXTERNAL = "external"

class ErrorContext:
    """Error context information"""
    
    def __init__(
        self,
        error: Exception,
        severity: ErrorSeverity,
        category: ErrorCategory,
        source: str,
        context: Optional[dict] = None
    ):
        self.error = error
        self.severity = severity
        self.category = category
        self.source = source
        self.context = context or {}
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()
        
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'error': str(self.error),
            'error_type': self.error.__class__.__name__,
            'severity': self.severity.value,
            'category': self.category.value,
            'source': self.source,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'traceback': self.traceback
        }

class ErrorHandler:
    """Error handling system"""
    
    def __init__(self):
        self.handlers: Dict[Type[Exception], List[Callable]] = {}
        self.fallback_handlers: List[Callable] = []
        self.error_history: List[ErrorContext] = []
        self.max_history = 1000
        
    def register_handler(
        self,
        exception_type: Type[Exception],
        handler: Callable
    ):
        """Register error handler"""
        if exception_type not in self.handlers:
            self.handlers[exception_type] = []
        self.handlers[exception_type].append(handler)
        
    def register_fallback(
        self,
        handler: Callable
    ):
        """Register fallback handler"""
        self.fallback_handlers.append(handler)
        
    async def handle_error(
        self,
        error: Exception,
        severity: ErrorSeverity,
        category: ErrorCategory,
        source: str,
        context: Optional[dict] = None
    ) -> bool:
        """Handle error"""
        # Create error context
        error_ctx = ErrorContext(
            error,
            severity,
            category,
            source,
            context
        )
        
        # Add to history
        self._add_to_history(error_ctx)
        
        # Find handlers
        handlers = self._get_handlers(error)
        
        # Execute handlers
        handled = False
        for handler in handlers:
            try:
                result = await handler(error_ctx)
                if result:
                    handled = True
            except Exception as e:
                logger.error(
                    f"Error handler failed: {e}"
                )
                
        return handled
        
    def get_recent_errors(
        self,
        count: int = 10
    ) -> List[ErrorContext]:
        """Get recent errors"""
        return self.error_history[-count:]
        
    def _add_to_history(
        self,
        error_ctx: ErrorContext
    ):
        """Add error to history"""
        self.error_history.append(error_ctx)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
            
    def _get_handlers(
        self,
        error: Exception
    ) -> List[Callable]:
        """Get handlers for error"""
        handlers = []
        
        # Get specific handlers
        for exc_type, type_handlers in self.handlers.items():
            if isinstance(error, exc_type):
                handlers.extend(type_handlers)
                
        # Add fallback handlers
        handlers.extend(self.fallback_handlers)
        
        return handlers
```

### 2. Error Recovery System

Implementation of error recovery strategies:

```python
class RecoveryStrategy(ABC):
    """Base recovery strategy"""
    
    @abstractmethod
    async def attempt_recovery(
        self,
        error_ctx: ErrorContext
    ) -> bool:
        """Attempt error recovery"""
        pass

class RetryStrategy(RecoveryStrategy):
    """Retry-based recovery strategy"""
    
    def __init__(
        self,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0
    ):
        self.max_retries = max_retries
        self.delay = delay
        self.backoff_factor = backoff_factor
        
    async def attempt_recovery(
        self,
        error_ctx: ErrorContext
    ) -> bool:
        """Attempt recovery with retries"""
        operation = error_ctx.context.get('operation')
        if not operation:
            return False
            
        for attempt in range(self.max_retries):
            try:
                # Wait before retry
                await asyncio.sleep(
                    self.delay * (self.backoff_factor ** attempt)
                )
                
                # Attempt operation
                await operation()
                return True
                
            except Exception as e:
                logger.warning(
                    f"Retry attempt {attempt + 1} failed: {e}"
                )
                
        return False

class FallbackStrategy(RecoveryStrategy):
    """Fallback-based recovery strategy"""
    
    def __init__(self, fallbacks: List[Callable]):
        self.fallbacks = fallbacks
        
    async def attempt_recovery(
        self,
        error_ctx: ErrorContext
    ) -> bool:
        """Attempt recovery with fallbacks"""
        for fallback in self.fallbacks:
            try:
                await fallback(error_ctx.context)
                return True
            except Exception as e:
                logger.warning(
                    f"Fallback failed: {e}"
                )
                
        return False

class CircuitBreakerStrategy(RecoveryStrategy):
    """Circuit breaker recovery strategy"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_open = False
        
    async def attempt_recovery(
        self,
        error_ctx: ErrorContext
    ) -> bool:
        """Attempt recovery with circuit breaker"""
        if self.circuit_open:
            # Check if we can reset
            if self.last_failure_time:
                elapsed = (
                    datetime.now() - self.last_failure_time
                ).total_seconds()
                
                if elapsed >= self.reset_timeout:
                    self.reset()
                else:
                    return False
                    
        # Update failure count
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        # Check threshold
        if self.failure_count >= self.failure_threshold:
            self.circuit_open = True
            return False
            
        return True
        
    def reset(self):
        """Reset circuit breaker"""
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_open = False
```

## Fault Tolerance

### 1. Fault Tolerance System

Implementation of fault tolerance mechanisms:

```python
class FaultToleranceManager:
    """Fault tolerance management system"""
    
    def __init__(self):
        self.strategies: Dict[str, List[RecoveryStrategy]] = {}
        self.error_handler = ErrorHandler()
        
    def add_strategy(
        self,
        component: str,
        strategy: RecoveryStrategy
    ):
        """Add recovery strategy"""
        if component not in self.strategies:
            self.strategies[component] = []
        self.strategies[component].append(strategy)
        
    async def handle_fault(
        self,
        component: str,
        error: Exception,
        context: Optional[dict] = None
    ) -> bool:
        """Handle component fault"""
        if component not in self.strategies:
            return False
            
        # Create error context
        error_ctx = ErrorContext(
            error,
            ErrorSeverity.ERROR,
            ErrorCategory.SYSTEM,
            component,
            context
        )
        
        # Try recovery strategies
        for strategy in self.strategies[component]:
            try:
                if await strategy.attempt_recovery(error_ctx):
                    return True
            except Exception as e:
                logger.error(
                    f"Recovery strategy failed: {e}"
                )
                
        # Handle unrecovered error
        await self.error_handler.handle_error(
            error,
            ErrorSeverity.CRITICAL,
            ErrorCategory.SYSTEM,
            component,
            context
        )
        
        return False

class HealthCheck:
    """Component health check"""
    
    def __init__(
        self,
        component: str,
        check_func: Callable
    ):
        self.component = component
        self.check_func = check_func
        self.last_check = None
        self.last_status = None
        
    async def check_health(self) -> bool:
        """Perform health check"""
        try:
            result = await self.check_func()
            self.last_check = datetime.now()
            self.last_status = result
            return result
        except Exception as e:
            logger.error(
                f"Health check failed: {e}"
            )
            self.last_status = False
            return False

class FaultMonitor:
    """System fault monitoring"""
    
    def __init__(
        self,
        fault_manager: FaultToleranceManager
    ):
        self.fault_manager = fault_manager
        self.health_checks: Dict[str, HealthCheck] = {}
        self.monitoring = False
        
    def add_health_check(
        self,
        component: str,
        check_func: Callable
    ):
        """Add component health check"""
        self.health_checks[component] = HealthCheck(
            component,
            check_func
        )
        
    async def start_monitoring(
        self,
        interval: float = 60.0
    ):
        """Start health monitoring"""
        self.monitoring = True
        
        while self.monitoring:
            for component, check in self.health_checks.items():
                healthy = await check.check_health()
                
                if not healthy:
                    await self.fault_manager.handle_fault(
                        component,
                        Exception("Health check failed"),
                        {
                            'last_check': check.last_check,
                            'last_status': check.last_status
                        }
                    )
                    
            await asyncio.sleep(interval)
            
    async def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring = False
```

## Error Reporting

### 1. Error Reporting System

Implementation of error reporting:

```python
class ErrorReport:
    """Error report generation"""
    
    def __init__(
        self,
        error_handler: ErrorHandler
    ):
        self.error_handler = error_handler
        
    def generate_report(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None
    ) -> dict:
        """Generate error report"""
        errors = self.error_handler.error_history
        
        # Filter errors
        if start_time:
            errors = [
                e for e in errors
                if e.timestamp >= start_time
            ]
            
        if end_time:
            errors = [
                e for e in errors
                if e.timestamp <= end_time
            ]
            
        if severity:
            errors = [
                e for e in errors
                if e.severity == severity
            ]
            
        if category:
            errors = [
                e for e in errors
                if e.category == category
            ]
            
        # Generate statistics
        stats = {
            'total_errors': len(errors),
            'by_severity': self._count_by_field(
                errors,
                'severity'
            ),
            'by_category': self._count_by_field(
                errors,
                'category'
            ),
            'by_source': self._count_by_field(
                errors,
                'source'
            ),
            'timeline': self._generate_timeline(errors)
        }
        
        return {
            'statistics': stats,
            'errors': [e.to_dict() for e in errors]
        }
        
    def _count_by_field(
        self,
        errors: List[ErrorContext],
        field: str
    ) -> dict:
        """Count errors by field"""
        counts = {}
        for error in errors:
            value = getattr(error, field)
            if isinstance(value, Enum):
                value = value.value
            counts[value] = counts.get(value, 0) + 1
        return counts
        
    def _generate_timeline(
        self,
        errors: List[ErrorContext]
    ) -> dict:
        """Generate error timeline"""
        timeline = {}
        for error in errors:
            date = error.timestamp.date().isoformat()
            timeline[date] = timeline.get(date, 0) + 1
        return timeline

class AlertSystem:
    """Error alerting system"""
    
    def __init__(self):
        self.alert_rules: Dict[str, dict] = {}
        self.alert_handlers: Dict[str, List[Callable]] = {}
        
    def add_rule(
        self,
        name: str,
        condition: Callable,
        severity: ErrorSeverity,
        cooldown: float = 300.0
    ):
        """Add alert rule"""
        self.alert_rules[name] = {
            'condition': condition,
            'severity': severity,
            'cooldown': cooldown,
            'last_alert': None
        }
        
    def add_handler(
        self,
        name: str,
        handler: Callable
    ):
        """Add alert handler"""
        if name not in self.alert_handlers:
            self.alert_handlers[name] = []
        self.alert_handlers[name].append(handler)
        
    async def check_alerts(
        self,
        error_ctx: ErrorContext
    ):
        """Check alert rules"""
        now = datetime.now()
        
        for name, rule in self.alert_rules.items():
            # Check cooldown
            if rule['last_alert']:
                elapsed = (
                    now - rule['last_alert']
                ).total_seconds()
                if elapsed < rule['cooldown']:
                    continue
                    
            # Check condition
            if await rule['condition'](error_ctx):
                # Trigger alert
                rule['last_alert'] = now
                await self._trigger_alert(
                    name,
                    error_ctx
                )
                
    async def _trigger_alert(
        self,
        rule_name: str,
        error_ctx: ErrorContext
    ):
        """Trigger alert handlers"""
        if rule_name in self.alert_handlers:
            for handler in self.alert_handlers[rule_name]:
                try:
                    await handler(error_ctx)
                except Exception as e:
                    logger.error(
                        f"Alert handler failed: {e}"
                    )
```

Remember to:
- Handle errors appropriately
- Implement recovery strategies
- Monitor system health
- Generate error reports
- Set up alerting
- Document error handling
- Test recovery mechanisms