# OpenHands Security and Testing Guide

This guide covers security implementation, testing strategies, and quality assurance in OpenHands.

## Table of Contents
1. [Security System](#security-system)
2. [Testing Framework](#testing-framework)
3. [Quality Assurance](#quality-assurance)
4. [Implementation Examples](#implementation-examples)
5. [Best Practices](#best-practices)

## Security System

### Security Analyzer

The security system is built around the `SecurityAnalyzer` class that monitors and analyzes all events:

```python
from openhands.events import EventStream, EventStreamSubscriber
from openhands.events.action import Action, ActionSecurityRisk

class SecurityAnalyzer:
    def __init__(self, event_stream: EventStream):
        self.event_stream = event_stream
        self.event_stream.subscribe(
            EventStreamSubscriber.SECURITY_ANALYZER,
            self.on_event,
            str(uuid4())
        )
    
    async def on_event(self, event: Event) -> None:
        """Analyze events for security risks"""
        if isinstance(event, Action):
            event.security_risk = await self.security_risk(event)
            await self.act(event)
    
    async def security_risk(self, event: Action) -> ActionSecurityRisk:
        """Evaluate action security risk"""
        raise NotImplementedError(
            'Need to implement security_risk method'
        )
```

### Custom Security Implementation

```python
class CustomSecurityAnalyzer(SecurityAnalyzer):
    def __init__(self, event_stream: EventStream):
        super().__init__(event_stream)
        self.risk_patterns = {
            "file_access": r"(\.\.\/|\/etc\/|\/root\/)",
            "system_commands": r"(rm\s+-rf|sudo|chmod\s+777)",
            "network_access": r"(0\.0\.0\.0|\/etc\/hosts)"
        }
    
    async def security_risk(self, event: Action) -> ActionSecurityRisk:
        """Evaluate security risk of an action"""
        risk_level = ActionSecurityRisk.NONE
        
        # Check action content against patterns
        action_str = str(event)
        for pattern_type, pattern in self.risk_patterns.items():
            if re.search(pattern, action_str):
                if pattern_type == "system_commands":
                    risk_level = ActionSecurityRisk.HIGH
                elif pattern_type == "file_access":
                    risk_level = ActionSecurityRisk.MEDIUM
                else:
                    risk_level = ActionSecurityRisk.LOW
        
        return risk_level
    
    async def act(self, event: Event) -> None:
        """Handle security risks"""
        if not hasattr(event, 'security_risk'):
            return
            
        if event.security_risk >= ActionSecurityRisk.HIGH:
            # Block high-risk actions
            logger.warning(f"Blocked high-risk action: {event}")
            return
            
        if event.security_risk >= ActionSecurityRisk.MEDIUM:
            # Require confirmation for medium-risk actions
            event.require_confirmation = True
```

## Testing Framework

### Unit Testing

OpenHands uses pytest for testing. Here's how to structure tests:

1. **Event Stream Testing**
```python
import pytest
from openhands.events import EventStream, EventSource
from openhands.events.observation import NullObservation

def test_event_stream_basic():
    """Test basic event stream functionality"""
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('test_session', file_store)
    
    # Add test event
    event_stream.add_event(
        NullObservation('test'),
        EventSource.AGENT
    )
    
    # Verify event
    events = list(event_stream.get_events())
    assert len(events) == 1
    assert events[0].content == 'test'
    assert events[0].source == EventSource.AGENT
```

2. **Security Testing**
```python
@pytest.mark.asyncio
async def test_security_analyzer():
    """Test security analysis functionality"""
    event_stream = EventStream('test_session', file_store)
    analyzer = CustomSecurityAnalyzer(event_stream)
    
    # Test high-risk action
    action = Action(command="rm -rf /")
    risk_level = await analyzer.security_risk(action)
    assert risk_level == ActionSecurityRisk.HIGH
    
    # Test medium-risk action
    action = Action(command="cat ../config.txt")
    risk_level = await analyzer.security_risk(action)
    assert risk_level == ActionSecurityRisk.MEDIUM
```

### Integration Testing

1. **System Integration Tests**
```python
@pytest.mark.integration
async def test_system_integration():
    """Test complete system workflow"""
    # Setup components
    event_stream = EventStream('test_session', file_store)
    security = SecurityAnalyzer(event_stream)
    agent = Agent(config)
    
    # Test workflow
    action = await agent.process_input("test command")
    events = list(event_stream.get_events())
    
    # Verify results
    assert len(events) == 2  # Input and response
    assert events[1].security_risk == ActionSecurityRisk.NONE
```

2. **API Testing**
```python
from fastapi.testclient import TestClient
from openhands.server.app import app

client = TestClient(app)

def test_api_security():
    """Test API security measures"""
    # Test unauthorized access
    response = client.get("/api/secure")
    assert response.status_code == 401
    
    # Test with invalid token
    response = client.get(
        "/api/secure",
        headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == 401
    
    # Test with valid token
    response = client.get(
        "/api/secure",
        headers={"Authorization": "Bearer valid_token"}
    )
    assert response.status_code == 200
```

## Quality Assurance

### 1. Code Quality Checks

```python
class CodeQualityChecker:
    def __init__(self):
        self.rules = {
            "complexity": self._check_complexity,
            "documentation": self._check_documentation,
            "style": self._check_style
        }
    
    def check_code(self, code: str) -> dict:
        """Run all quality checks"""
        results = {}
        for rule_name, check_func in self.rules.items():
            results[rule_name] = check_func(code)
        return results
    
    def _check_complexity(self, code: str) -> dict:
        """Check code complexity"""
        # Implement complexity metrics
        return {"status": "pass", "metrics": {}}
    
    def _check_documentation(self, code: str) -> dict:
        """Check documentation coverage"""
        # Check docstrings and comments
        return {"status": "pass", "coverage": 100}
    
    def _check_style(self, code: str) -> dict:
        """Check code style"""
        # Check PEP 8 compliance
        return {"status": "pass", "violations": []}
```

### 2. Performance Testing

```python
class PerformanceTest:
    def __init__(self):
        self.metrics = {}
    
    async def measure_performance(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> dict:
        """Measure function performance"""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            result = await func(*args, **kwargs)
            success = True
        except Exception as e:
            result = str(e)
            success = False
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        return {
            "success": success,
            "execution_time": end_time - start_time,
            "memory_usage": end_memory - start_memory,
            "result": result
        }
```

## Implementation Examples

### 1. Custom Security Rules

```python
class SecurityRules:
    def __init__(self):
        self.rules = []
        self._load_default_rules()
    
    def _load_default_rules(self):
        self.rules.extend([
            {
                "pattern": r"rm\s+-rf\s+/",
                "risk": ActionSecurityRisk.HIGH,
                "message": "Dangerous system command"
            },
            {
                "pattern": r"\.\.\/",
                "risk": ActionSecurityRisk.MEDIUM,
                "message": "Directory traversal attempt"
            },
            {
                "pattern": r"chmod\s+777",
                "risk": ActionSecurityRisk.HIGH,
                "message": "Unsafe permission change"
            }
        ])
    
    def add_rule(self, pattern: str, risk: ActionSecurityRisk, message: str):
        """Add custom security rule"""
        self.rules.append({
            "pattern": pattern,
            "risk": risk,
            "message": message
        })
    
    def check_action(self, action: str) -> list[dict]:
        """Check action against all rules"""
        violations = []
        for rule in self.rules:
            if re.search(rule["pattern"], action):
                violations.append({
                    "risk": rule["risk"],
                    "message": rule["message"]
                })
        return violations
```

### 2. Test Fixtures

```python
@pytest.fixture
def event_stream_fixture():
    """Fixture for testing event stream"""
    file_store = get_file_store('local', temp_dir)
    stream = EventStream('test_session', file_store)
    yield stream
    stream.close()

@pytest.fixture
def security_analyzer_fixture(event_stream_fixture):
    """Fixture for testing security analyzer"""
    analyzer = CustomSecurityAnalyzer(event_stream_fixture)
    yield analyzer
    analyzer.close()

@pytest.fixture
def agent_fixture(event_stream_fixture):
    """Fixture for testing agent"""
    config = AgentConfig()
    agent = Agent(config, event_stream_fixture)
    yield agent
    agent.cleanup()
```

### 3. Performance Monitoring

```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
        self.thresholds = {
            "response_time": 1.0,  # seconds
            "memory_usage": 100_000_000  # bytes
        }
    
    async def monitor_function(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> tuple[Any, dict]:
        """Monitor function performance"""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        result = await func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        metrics = {
            "execution_time": end_time - start_time,
            "memory_usage": end_memory - start_memory
        }
        
        self._check_thresholds(metrics)
        self._update_metrics(func.__name__, metrics)
        
        return result, metrics
    
    def _check_thresholds(self, metrics: dict):
        """Check if metrics exceed thresholds"""
        if metrics["execution_time"] > self.thresholds["response_time"]:
            logger.warning(
                f"Slow execution: {metrics['execution_time']:.2f}s"
            )
        
        if metrics["memory_usage"] > self.thresholds["memory_usage"]:
            logger.warning(
                f"High memory usage: {metrics['memory_usage']/1_000_000:.1f}MB"
            )
    
    def _update_metrics(self, func_name: str, metrics: dict):
        """Update historical metrics"""
        if func_name not in self.metrics:
            self.metrics[func_name] = []
        self.metrics[func_name].append(metrics)
```

## Best Practices

### 1. Security Best Practices

1. **Input Validation**
```python
def validate_input(input_data: Any) -> bool:
    """Validate input data"""
    if isinstance(input_data, str):
        # Check for dangerous patterns
        dangerous_patterns = [
            r"\.\.\/",
            r";\s*rm",
            r">\s*/etc/passwd"
        ]
        return not any(
            re.search(pattern, input_data)
            for pattern in dangerous_patterns
        )
    return True
```

2. **Access Control**
```python
def check_permissions(
    user: str,
    resource: str,
    action: str
) -> bool:
    """Check user permissions"""
    permission_matrix = {
        "admin": ["read", "write", "delete"],
        "user": ["read", "write"],
        "guest": ["read"]
    }
    
    user_role = get_user_role(user)
    return action in permission_matrix.get(user_role, [])
```

### 2. Testing Best Practices

1. **Test Organization**
```python
class TestSecurity:
    """Security-related tests"""
    
    def test_input_validation(self):
        """Test input validation"""
        assert validate_input("normal input")
        assert not validate_input("../etc/passwd")
    
    def test_permissions(self):
        """Test permission system"""
        assert check_permissions("admin", "file.txt", "delete")
        assert not check_permissions("guest", "file.txt", "delete")
```

2. **Performance Testing**
```python
@pytest.mark.performance
async def test_performance():
    """Test performance metrics"""
    monitor = PerformanceMonitor()
    
    result, metrics = await monitor.monitor_function(
        heavy_operation,
        input_data
    )
    
    assert metrics["execution_time"] < 1.0
    assert metrics["memory_usage"] < 100_000_000
```

### 3. Quality Assurance Best Practices

1. **Code Review Checklist**
```python
class CodeReviewChecker:
    def __init__(self):
        self.checklist = [
            self._check_documentation,
            self._check_error_handling,
            self._check_security,
            self._check_performance
        ]
    
    def review_code(self, code: str) -> dict:
        """Run all code review checks"""
        results = {}
        for check in self.checklist:
            results[check.__name__] = check(code)
        return results
    
    def _check_documentation(self, code: str) -> dict:
        """Check documentation quality"""
        return {
            "has_docstrings": True,
            "coverage": 100
        }
    
    def _check_error_handling(self, code: str) -> dict:
        """Check error handling"""
        return {
            "has_try_except": True,
            "handles_exceptions": True
        }
```

Remember to:
- Implement comprehensive security checks
- Write thorough tests for all components
- Monitor performance metrics
- Follow security best practices
- Maintain code quality standards
- Document security and testing procedures