# OpenHands Practical Examples Guide

This guide provides practical examples and common use cases for developing with OpenHands.

## Table of Contents
1. [Common Use Cases](#common-use-cases)
2. [Development Patterns](#development-patterns)
3. [Integration Examples](#integration-examples)
4. [Troubleshooting Guide](#troubleshooting-guide)

## Common Use Cases

### 1. Creating a Code Review Agent

This example shows how to create an agent that performs automated code reviews:

```python
from openhands.controller.agent import Agent
from openhands.events.action import Action
from openhands.events import Event, EventSource
from openhands.llm import LLM

class CodeReviewAgent(Agent):
    def __init__(self, llm: LLM, config: 'AgentConfig'):
        super().__init__(llm, config)
        self.review_patterns = {
            'style': [
                'inconsistent indentation',
                'line too long',
                'missing docstring'
            ],
            'security': [
                'hardcoded credentials',
                'sql injection',
                'command injection'
            ],
            'performance': [
                'inefficient loop',
                'unnecessary allocation',
                'redundant computation'
            ]
        }
    
    async def step(self, state: 'State') -> 'Action':
        """Process the current state and return next action"""
        # Get the latest input
        latest_event = state.get_latest_input()
        if not latest_event:
            return Action(message="No input to process")
        
        # If it's a code review request
        if self._is_code_review_request(latest_event):
            code = self._extract_code(latest_event)
            review_result = await self._review_code(code)
            return Action(
                message=self._format_review(review_result),
                source=EventSource.AGENT
            )
        
        return Action(message="Please provide code for review")
    
    async def _review_code(self, code: str) -> dict:
        """Perform code review using LLM"""
        prompt = self._create_review_prompt(code)
        response = await self.llm.generate(prompt)
        
        # Parse LLM response into structured format
        issues = self._parse_review_response(response)
        return {
            'issues': issues,
            'summary': self._generate_summary(issues)
        }
    
    def _create_review_prompt(self, code: str) -> str:
        return f"""
        Please review the following code for:
        1. Style issues
        2. Security concerns
        3. Performance problems
        4. Best practices

        Code to review:
        ```
        {code}
        ```
        
        Provide specific issues and recommendations.
        """
    
    def _parse_review_response(self, response: str) -> list[dict]:
        # Parse LLM response into structured issues
        issues = []
        current_category = None
        
        for line in response.split('\n'):
            if any(cat in line.lower() for cat in ['style:', 'security:', 'performance:']):
                current_category = line.split(':')[0].lower()
            elif line.strip() and current_category:
                issues.append({
                    'category': current_category,
                    'description': line.strip(),
                    'severity': self._determine_severity(line)
                })
        
        return issues
    
    def _determine_severity(self, issue: str) -> str:
        """Determine issue severity based on content"""
        if any(p in issue.lower() for p in self.review_patterns['security']):
            return 'high'
        elif any(p in issue.lower() for p in self.review_patterns['performance']):
            return 'medium'
        return 'low'
```

### 2. Implementing a Documentation Generator

Example of an agent that generates documentation from code:

```python
class DocGeneratorAgent(Agent):
    def __init__(self, llm: LLM, config: 'AgentConfig'):
        super().__init__(llm, config)
        self.doc_templates = {
            'function': self._function_template,
            'class': self._class_template,
            'module': self._module_template
        }
    
    async def step(self, state: 'State') -> 'Action':
        """Process current state and generate documentation"""
        latest_event = state.get_latest_input()
        if not latest_event:
            return Action(message="No input to process")
        
        code = self._extract_code(latest_event)
        doc_type = self._determine_doc_type(code)
        
        # Generate documentation
        docs = await self._generate_docs(code, doc_type)
        return Action(
            message=docs,
            source=EventSource.AGENT
        )
    
    async def _generate_docs(self, code: str, doc_type: str) -> str:
        """Generate documentation using LLM"""
        template = self.doc_templates.get(doc_type, self._function_template)
        prompt = template(code)
        
        response = await self.llm.generate(prompt)
        return self._format_documentation(response, doc_type)
    
    def _function_template(self, code: str) -> str:
        return f"""
        Generate documentation for this function:
        ```python
        {code}
        ```
        Include:
        1. Description
        2. Parameters
        3. Return value
        4. Examples
        """
    
    def _format_documentation(self, docs: str, doc_type: str) -> str:
        """Format documentation in markdown"""
        return f"""
        # {doc_type.title()} Documentation
        
        {docs}
        
        Generated by OpenHands DocGenerator
        """
```

### 3. Creating a Test Generator

Example of an agent that generates test cases:

```python
class TestGeneratorAgent(Agent):
    def __init__(self, llm: LLM, config: 'AgentConfig'):
        super().__init__(llm, config)
        self.test_frameworks = {
            'pytest': self._generate_pytest,
            'unittest': self._generate_unittest
        }
    
    async def step(self, state: 'State') -> 'Action':
        """Generate test cases for given code"""
        latest_event = state.get_latest_input()
        if not latest_event:
            return Action(message="No input to process")
        
        code = self._extract_code(latest_event)
        framework = self._determine_framework(latest_event)
        
        # Generate tests
        tests = await self._generate_tests(code, framework)
        return Action(
            message=tests,
            source=EventSource.AGENT
        )
    
    async def _generate_tests(self, code: str, framework: str) -> str:
        """Generate test cases using LLM"""
        generator = self.test_frameworks.get(framework, self._generate_pytest)
        return await generator(code)
    
    async def _generate_pytest(self, code: str) -> str:
        prompt = f"""
        Generate pytest test cases for this code:
        ```python
        {code}
        ```
        Include:
        1. Happy path tests
        2. Edge cases
        3. Error cases
        4. Fixtures if needed
        """
        
        response = await self.llm.generate(prompt)
        return self._format_test_cases(response)
```

## Development Patterns

### 1. Event-Driven Processing

Example of implementing event-driven processing:

```python
class EventProcessor:
    def __init__(self, event_stream: EventStream):
        self.event_stream = event_stream
        self.handlers = {
            'code_review': self._handle_code_review,
            'documentation': self._handle_documentation,
            'test_generation': self._handle_test_generation
        }
    
    async def process_events(self):
        """Process events from stream"""
        async for event in self.event_stream:
            if event.type in self.handlers:
                await self.handlers[event.type](event)
    
    async def _handle_code_review(self, event: Event):
        """Handle code review events"""
        reviewer = CodeReviewAgent(self.llm, self.config)
        result = await reviewer.process(event)
        self.event_stream.add_event(result, EventSource.AGENT)
```

### 2. Pipeline Processing

Example of implementing a processing pipeline:

```python
class ProcessingPipeline:
    def __init__(self):
        self.stages = []
        self.results = {}
    
    def add_stage(
        self,
        name: str,
        processor: Callable,
        required: bool = True
    ):
        """Add a processing stage"""
        self.stages.append({
            'name': name,
            'processor': processor,
            'required': required
        })
    
    async def process(self, input_data: Any) -> dict:
        """Run the processing pipeline"""
        current_data = input_data
        
        for stage in self.stages:
            try:
                result = await stage['processor'](current_data)
                self.results[stage['name']] = result
                current_data = result
            except Exception as e:
                if stage['required']:
                    raise
                logger.warning(
                    f"Optional stage {stage['name']} failed: {e}"
                )
        
        return self.results
```

### 3. State Management

Example of implementing state management:

```python
class StateManager:
    def __init__(self):
        self.states = {}
        self._lock = asyncio.Lock()
    
    async def get_state(self, key: str) -> Any:
        """Get state value"""
        async with self._lock:
            return self.states.get(key)
    
    async def set_state(self, key: str, value: Any):
        """Set state value"""
        async with self._lock:
            self.states[key] = value
    
    async def update_state(
        self,
        key: str,
        updater: Callable[[Any], Any]
    ):
        """Update state with a function"""
        async with self._lock:
            current = self.states.get(key)
            self.states[key] = updater(current)
```

## Integration Examples

### 1. Integrating with External Services

```python
class ExternalServiceIntegration:
    def __init__(self, config: dict):
        self.config = config
        self.clients = {}
    
    async def setup(self):
        """Setup service clients"""
        for service, cfg in self.config.items():
            self.clients[service] = await self._create_client(
                service,
                cfg
            )
    
    async def _create_client(
        self,
        service: str,
        config: dict
    ) -> Any:
        """Create service client"""
        if service == 'github':
            return GithubClient(config)
        elif service == 'gitlab':
            return GitlabClient(config)
        else:
            raise ValueError(f"Unknown service: {service}")
```

### 2. Database Integration

```python
class DatabaseIntegration:
    def __init__(self, config: dict):
        self.config = config
        self.connections = {}
    
    async def connect(self):
        """Setup database connections"""
        for db_name, cfg in self.config.items():
            self.connections[db_name] = await self._create_connection(
                db_name,
                cfg
            )
    
    async def _create_connection(
        self,
        db_name: str,
        config: dict
    ) -> Any:
        """Create database connection"""
        if config['type'] == 'postgres':
            return await asyncpg.connect(**config)
        elif config['type'] == 'mysql':
            return await aiomysql.connect(**config)
        else:
            raise ValueError(f"Unknown database type: {config['type']}")
```

## Troubleshooting Guide

### 1. Common Issues and Solutions

```python
class TroubleshootingGuide:
    def __init__(self):
        self.common_issues = {
            'connection_error': self._handle_connection_error,
            'timeout_error': self._handle_timeout_error,
            'memory_error': self._handle_memory_error
        }
    
    async def diagnose(self, error: Exception) -> str:
        """Diagnose and provide solution"""
        error_type = type(error).__name__
        handler = self.common_issues.get(
            error_type,
            self._handle_unknown_error
        )
        return await handler(error)
    
    async def _handle_connection_error(self, error: Exception) -> str:
        return """
        Connection Error Detected
        
        Common causes:
        1. Network connectivity issues
        2. Service unavailable
        3. Invalid credentials
        
        Solutions:
        1. Check network connection
        2. Verify service status
        3. Validate credentials
        """
```

### 2. Debugging Tools

```python
class DebugTools:
    def __init__(self):
        self.logs = []
        self.metrics = {}
    
    def log_event(self, event: dict):
        """Log debug event"""
        self.logs.append({
            'timestamp': datetime.now().isoformat(),
            'event': event
        })
    
    def track_metric(self, name: str, value: float):
        """Track performance metric"""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append({
            'timestamp': datetime.now().isoformat(),
            'value': value
        })
    
    def get_report(self) -> dict:
        """Generate debug report"""
        return {
            'logs': self.logs[-100:],  # Last 100 logs
            'metrics': {
                name: self._analyze_metric(values)
                for name, values in self.metrics.items()
            }
        }
    
    def _analyze_metric(self, values: list) -> dict:
        """Analyze metric values"""
        numbers = [v['value'] for v in values]
        return {
            'min': min(numbers),
            'max': max(numbers),
            'avg': sum(numbers) / len(numbers),
            'count': len(numbers)
        }
```

Remember to:
- Adapt examples to your specific needs
- Follow error handling best practices
- Implement proper logging
- Add appropriate documentation
- Include test cases
- Consider performance implications