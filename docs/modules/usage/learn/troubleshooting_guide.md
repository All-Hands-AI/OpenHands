# OpenHands Troubleshooting and Diagnostics Guide

This guide provides comprehensive information about troubleshooting, debugging, and diagnosing issues in OpenHands systems.

## Table of Contents
1. [Diagnostic Tools](#diagnostic-tools)
2. [Common Issues and Solutions](#common-issues-and-solutions)
3. [Performance Analysis](#performance-analysis)
4. [System Health Monitoring](#system-health-monitoring)

## Diagnostic Tools

### 1. System Diagnostics Tool

A comprehensive diagnostic tool for OpenHands systems:

```python
from dataclasses import dataclass
from typing import List, Dict, Any
import psutil
import asyncio
import logging
import traceback

@dataclass
class SystemHealth:
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    event_queue_size: int
    active_agents: int
    error_count: int
    warnings: List[str]

class SystemDiagnostics:
    def __init__(self):
        self.logger = logging.getLogger("diagnostics")
        self.error_threshold = 100
        self.warning_threshold = 50
        self.metrics_history = []
        
    async def run_diagnostics(self) -> SystemHealth:
        """Run comprehensive system diagnostics"""
        try:
            # Collect system metrics
            cpu = psutil.cpu_percent()
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            # Collect application metrics
            queue_size = await self._check_event_queue()
            active_agents = await self._count_active_agents()
            errors = await self._check_error_logs()
            warnings = await self._check_system_warnings()
            
            health = SystemHealth(
                cpu_usage=cpu,
                memory_usage=memory,
                disk_usage=disk,
                event_queue_size=queue_size,
                active_agents=active_agents,
                error_count=len(errors),
                warnings=warnings
            )
            
            self.metrics_history.append(health)
            if len(self.metrics_history) > 1000:
                self.metrics_history.pop(0)
                
            return health
            
        except Exception as e:
            self.logger.error(f"Diagnostics failed: {e}")
            raise
            
    async def analyze_trends(self) -> Dict[str, Any]:
        """Analyze system health trends"""
        if not self.metrics_history:
            return {}
            
        return {
            'cpu_trend': self._calculate_trend(
                [m.cpu_usage for m in self.metrics_history]
            ),
            'memory_trend': self._calculate_trend(
                [m.memory_usage for m in self.metrics_history]
            ),
            'error_trend': self._calculate_trend(
                [m.error_count for m in self.metrics_history]
            )
        }
        
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "stable"
            
        avg_first_half = sum(values[:len(values)//2]) / (len(values)//2)
        avg_second_half = sum(values[len(values)//2:]) / (len(values)//2)
        
        diff = avg_second_half - avg_first_half
        if abs(diff) < 0.1:
            return "stable"
        return "increasing" if diff > 0 else "decreasing"
```

### 2. Log Analysis Tool

Advanced log analysis tool for identifying issues:

```python
class LogAnalyzer:
    def __init__(self, log_path: str):
        self.log_path = log_path
        self.patterns = {
            'error': r'ERROR.*',
            'warning': r'WARNING.*',
            'timeout': r'.*timeout.*',
            'memory': r'.*memory.*',
            'connection': r'.*connection.*failed.*'
        }
        
    async def analyze_logs(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze logs for the past N hours"""
        start_time = datetime.now() - timedelta(hours=hours)
        issues = {
            'errors': [],
            'warnings': [],
            'patterns': defaultdict(list)
        }
        
        async with aiofiles.open(self.log_path, 'r') as f:
            async for line in f:
                try:
                    timestamp = self._extract_timestamp(line)
                    if timestamp < start_time:
                        continue
                        
                    # Analyze line
                    if 'ERROR' in line:
                        issues['errors'].append(self._parse_log_entry(line))
                    elif 'WARNING' in line:
                        issues['warnings'].append(self._parse_log_entry(line))
                        
                    # Check patterns
                    for pattern_name, pattern in self.patterns.items():
                        if re.search(pattern, line, re.IGNORECASE):
                            issues['patterns'][pattern_name].append(
                                self._parse_log_entry(line)
                            )
                            
                except Exception as e:
                    logger.error(f"Error parsing log line: {e}")
                    
        return self._summarize_issues(issues)
        
    def _parse_log_entry(self, line: str) -> dict:
        """Parse log entry into structured format"""
        parts = line.split(' ')
        return {
            'timestamp': parts[0],
            'level': parts[1],
            'message': ' '.join(parts[2:]),
            'context': self._extract_context(line)
        }
        
    def _extract_context(self, line: str) -> dict:
        """Extract context information from log line"""
        context = {}
        try:
            # Extract common patterns
            if 'agent=' in line:
                context['agent'] = re.search(r'agent=(\w+)', line).group(1)
            if 'session=' in line:
                context['session'] = re.search(r'session=(\w+)', line).group(1)
            if 'error=' in line:
                context['error'] = re.search(r'error="([^"]+)"', line).group(1)
        except Exception:
            pass
        return context
```

## Common Issues and Solutions

### 1. Issue Resolution System

System for tracking and resolving common issues:

```python
class IssueResolver:
    def __init__(self):
        self.solutions = {
            'memory_leak': self._handle_memory_leak,
            'connection_timeout': self._handle_timeout,
            'agent_stuck': self._handle_stuck_agent,
            'event_queue_full': self._handle_queue_full
        }
        
    async def resolve_issue(self, issue_type: str, context: dict) -> dict:
        """Attempt to resolve an issue"""
        if issue_type not in self.solutions:
            raise ValueError(f"Unknown issue type: {issue_type}")
            
        try:
            solution = await self.solutions[issue_type](context)
            return {
                'status': 'resolved',
                'solution': solution,
                'context': context
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'context': context
            }
            
    async def _handle_memory_leak(self, context: dict) -> str:
        """Handle memory leak issues"""
        # Check memory usage patterns
        memory_info = psutil.Process().memory_info()
        
        if memory_info.rss > context.get('threshold', 1e9):
            # Attempt to free memory
            import gc
            gc.collect()
            
            # Check if helped
            new_memory = psutil.Process().memory_info()
            if new_memory.rss < memory_info.rss:
                return "Memory freed successfully"
                
        return "Memory usage within normal range"
        
    async def _handle_stuck_agent(self, context: dict) -> str:
        """Handle stuck agent issues"""
        agent_id = context.get('agent_id')
        if not agent_id:
            raise ValueError("Agent ID required")
            
        # Check agent status
        agent = await self._get_agent(agent_id)
        if not agent:
            return "Agent not found"
            
        if await self._is_agent_stuck(agent):
            # Reset agent
            await self._reset_agent(agent)
            return "Agent reset successfully"
            
        return "Agent operating normally"
```

### 2. Error Recovery System

System for handling and recovering from errors:

```python
class ErrorRecovery:
    def __init__(self):
        self.recovery_strategies = {
            'connection': self._recover_connection,
            'timeout': self._recover_timeout,
            'resource': self._recover_resource,
            'state': self._recover_state
        }
        
    async def attempt_recovery(
        self,
        error: Exception,
        context: dict
    ) -> bool:
        """Attempt to recover from an error"""
        error_type = self._classify_error(error)
        
        if error_type in self.recovery_strategies:
            try:
                await self.recovery_strategies[error_type](context)
                return True
            except Exception as e:
                logger.error(f"Recovery failed: {e}")
                return False
                
        return False
        
    def _classify_error(self, error: Exception) -> str:
        """Classify error type"""
        if isinstance(error, ConnectionError):
            return 'connection'
        elif isinstance(error, TimeoutError):
            return 'timeout'
        elif isinstance(error, MemoryError):
            return 'resource'
        else:
            return 'unknown'
            
    async def _recover_connection(self, context: dict):
        """Recover from connection errors"""
        max_retries = context.get('max_retries', 3)
        retry_delay = context.get('retry_delay', 1)
        
        for attempt in range(max_retries):
            try:
                await self._reconnect(context)
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(retry_delay * (attempt + 1))
```

## Performance Analysis

### 1. Performance Profiler

System for profiling and analyzing performance:

```python
class PerformanceProfiler:
    def __init__(self):
        self.profiles = {}
        self.thresholds = {
            'response_time': 1.0,  # seconds
            'memory_usage': 100_000_000,  # bytes
            'cpu_usage': 80.0  # percent
        }
        
    async def start_profile(self, name: str):
        """Start profiling a section"""
        self.profiles[name] = {
            'start_time': time.time(),
            'start_memory': psutil.Process().memory_info().rss,
            'start_cpu': psutil.Process().cpu_percent()
        }
        
    async def end_profile(self, name: str) -> dict:
        """End profiling and get results"""
        if name not in self.profiles:
            raise ValueError(f"No profile started for {name}")
            
        profile = self.profiles[name]
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        end_cpu = psutil.Process().cpu_percent()
        
        results = {
            'duration': end_time - profile['start_time'],
            'memory_delta': end_memory - profile['start_memory'],
            'cpu_usage': end_cpu - profile['start_cpu']
        }
        
        # Check thresholds
        warnings = []
        if results['duration'] > self.thresholds['response_time']:
            warnings.append(f"Slow response: {results['duration']:.2f}s")
        if results['memory_delta'] > self.thresholds['memory_usage']:
            warnings.append(
                f"High memory usage: {results['memory_delta']/1_000_000:.1f}MB"
            )
        if results['cpu_usage'] > self.thresholds['cpu_usage']:
            warnings.append(f"High CPU usage: {results['cpu_usage']:.1f}%")
            
        results['warnings'] = warnings
        return results
```

## System Health Monitoring

### 1. Health Check System

Comprehensive system health monitoring:

```python
class HealthMonitor:
    def __init__(self):
        self.checks = {
            'memory': self._check_memory,
            'cpu': self._check_cpu,
            'disk': self._check_disk,
            'network': self._check_network,
            'agents': self._check_agents,
            'events': self._check_events
        }
        self.status_history = []
        
    async def run_health_check(self) -> dict:
        """Run all health checks"""
        results = {}
        status = 'healthy'
        
        for check_name, check_func in self.checks.items():
            try:
                check_result = await check_func()
                results[check_name] = check_result
                
                if check_result['status'] == 'critical':
                    status = 'critical'
                elif check_result['status'] == 'warning' and status != 'critical':
                    status = 'warning'
                    
            except Exception as e:
                results[check_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                status = 'critical'
                
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'checks': results
        }
        
        self.status_history.append(health_status)
        if len(self.status_history) > 1000:
            self.status_history.pop(0)
            
        return health_status
        
    async def get_health_trends(self) -> dict:
        """Analyze health trends"""
        if not self.status_history:
            return {}
            
        trends = {}
        for check_name in self.checks:
            status_counts = {
                'healthy': 0,
                'warning': 0,
                'critical': 0,
                'error': 0
            }
            
            for status in self.status_history:
                if check_name in status['checks']:
                    check_status = status['checks'][check_name]['status']
                    status_counts[check_status] += 1
                    
            total = len(self.status_history)
            trends[check_name] = {
                status: count/total * 100
                for status, count in status_counts.items()
            }
            
        return trends
```

### 2. Alert System

System for monitoring and alerting on issues:

```python
class AlertSystem:
    def __init__(self):
        self.alert_rules = {
            'memory_high': {
                'check': lambda x: x > 90,
                'metric': 'memory_usage',
                'severity': 'critical'
            },
            'cpu_high': {
                'check': lambda x: x > 80,
                'metric': 'cpu_usage',
                'severity': 'warning'
            },
            'error_spike': {
                'check': lambda x: x > 100,
                'metric': 'error_count',
                'severity': 'critical'
            }
        }
        self.active_alerts = {}
        
    async def check_alerts(self, metrics: dict):
        """Check metrics against alert rules"""
        new_alerts = {}
        
        for rule_name, rule in self.alert_rules.items():
            if rule['metric'] in metrics:
                value = metrics[rule['metric']]
                if rule['check'](value):
                    new_alerts[rule_name] = {
                        'metric': rule['metric'],
                        'value': value,
                        'severity': rule['severity'],
                        'timestamp': datetime.now().isoformat()
                    }
                    
        # Handle alert state changes
        await self._process_alert_changes(new_alerts)
        
    async def _process_alert_changes(self, new_alerts: dict):
        """Process changes in alert status"""
        # Check for new alerts
        for alert_name, alert in new_alerts.items():
            if alert_name not in self.active_alerts:
                await self._trigger_alert(alert_name, alert)
                
        # Check for resolved alerts
        for alert_name in list(self.active_alerts.keys()):
            if alert_name not in new_alerts:
                await self._resolve_alert(alert_name)
                
        self.active_alerts = new_alerts
        
    async def _trigger_alert(self, name: str, alert: dict):
        """Trigger a new alert"""
        logger.warning(f"Alert triggered: {name}")
        # Implement alert notification logic here
        
    async def _resolve_alert(self, name: str):
        """Mark alert as resolved"""
        logger.info(f"Alert resolved: {name}")
        # Implement alert resolution logic here
```

Remember to:
- Regularly monitor system health
- Set up appropriate alerts
- Implement proper error recovery
- Keep diagnostic logs
- Monitor performance metrics
- Document troubleshooting procedures
- Maintain system health checks