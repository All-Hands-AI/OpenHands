# OpenHands Common Development Scenarios

This guide covers real-world scenarios, common issues, and solutions that new developers often encounter when working with OpenHands.

## Common Development Scenarios

### 1. Agent Not Processing Input Correctly

#### Scenario
Agent is receiving input but not generating expected responses.

#### Diagnosis
```python
# 1. Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# 2. Add debug points in agent
class MyAgent(Agent):
    async def step(self, state: State) -> Action:
        # Debug input
        latest_event = state.get_latest_input()
        logger.debug(f"Processing input: {latest_event}")
        
        # Debug LLM call
        llm_response = await self.llm.generate(prompt)
        logger.debug(f"LLM response: {llm_response}")
        
        # Debug state
        logger.debug(f"Current state: {state.to_dict()}")
```

#### Common Causes and Solutions
1. **LLM Configuration**
```python
# Check LLM configuration
class MyAgent(Agent):
    def __init__(self, llm: LLM, config: Config):
        super().__init__(llm, config)
        # Verify LLM setup
        logger.debug(f"LLM config: {llm.config}")
        logger.debug(f"Agent config: {config}")
```

2. **State Management**
```python
# Implement state tracking
class MyAgent(Agent):
    def __init__(self, llm: LLM, config: Config):
        super().__init__(llm, config)
        self.state_history = []
        
    async def step(self, state: State) -> Action:
        # Track state changes
        self.state_history.append(state.copy())
        if len(self.state_history) > 10:
            self.state_history.pop(0)
```

3. **Event Processing**
```python
# Add event validation
class MyAgent(Agent):
    def _validate_event(self, event: Event) -> bool:
        if not event.message:
            logger.warning("Empty message in event")
            return False
        if not isinstance(event.message, str):
            logger.warning(f"Invalid message type: {type(event.message)}")
            return False
        return True
```

### 2. Runtime Execution Failures

#### Scenario
Runtime fails to execute actions or returns unexpected results.

#### Diagnosis
```python
# 1. Add runtime debugging
class DebugRuntime(Runtime):
    async def execute(self, action: Action) -> Observation:
        logger.debug(f"Executing action: {action}")
        try:
            result = await super().execute(action)
            logger.debug(f"Action result: {result}")
            return result
        except Exception as e:
            logger.error(f"Action failed: {e}")
            raise

# 2. Track runtime state
class RuntimeStateTracker:
    def __init__(self):
        self.actions = []
        self.results = []
        
    def track(self, action: Action, result: Observation):
        self.actions.append(action)
        self.results.append(result)
        
        if len(self.actions) > 100:
            self.actions.pop(0)
            self.results.pop(0)
```

#### Common Causes and Solutions
1. **Action Validation**
```python
class ValidatedRuntime(Runtime):
    def _validate_action(self, action: Action) -> bool:
        # Check action type
        if not hasattr(self, action.type):
            logger.error(f"Unsupported action type: {action.type}")
            return False
            
        # Check required fields
        required_fields = self._get_required_fields(action.type)
        for field in required_fields:
            if field not in action.data:
                logger.error(f"Missing required field: {field}")
                return False
                
        return True
```

2. **Resource Management**
```python
class ResourceManager:
    def __init__(self):
        self.active_resources = {}
        self.resource_limits = {}
        
    async def acquire(self, resource_type: str) -> bool:
        current = len(self.active_resources.get(resource_type, []))
        limit = self.resource_limits.get(resource_type, 10)
        
        if current >= limit:
            logger.warning(f"Resource limit reached: {resource_type}")
            return False
            
        self.active_resources.setdefault(resource_type, []).append(
            datetime.now()
        )
        return True
```

3. **Error Recovery**
```python
class RecoverableRuntime(Runtime):
    async def execute(self, action: Action) -> Observation:
        try:
            return await super().execute(action)
        except ResourceError:
            # Try to recover resources
            await self._cleanup_resources()
            return await super().execute(action)
        except TimeoutError:
            # Retry with increased timeout
            return await self._retry_with_timeout(action)
```

### 3. Event System Issues

#### Scenario
Events not being properly propagated or handled.

#### Diagnosis
```python
# 1. Event tracer
class EventTracer:
    def __init__(self, event_stream: EventStream):
        self.event_stream = event_stream
        self.traces = []
        
    async def start_tracing(self):
        self.event_stream.subscribe(
            EventStreamSubscriber.TRACER,
            self._trace_event
        )
        
    async def _trace_event(self, event: Event):
        trace = {
            'timestamp': datetime.now(),
            'event_type': type(event).__name__,
            'event_id': event.id,
            'source': event.source,
            'data': event.to_dict()
        }
        self.traces.append(trace)
```

#### Common Causes and Solutions
1. **Event Routing**
```python
class EventRouter:
    def __init__(self):
        self.routes = {}
        self.fallbacks = []
        
    async def route_event(self, event: Event):
        # Check specific routes
        handler = self.routes.get(event.type)
        if handler:
            await handler(event)
            return
            
        # Try fallbacks
        for fallback in self.fallbacks:
            if await fallback(event):
                return
                
        logger.warning(f"Unhandled event: {event.type}")
```

2. **Event Validation**
```python
class EventValidator:
    def __init__(self):
        self.validators = {}
        
    def add_validator(
        self,
        event_type: str,
        validator: Callable
    ):
        self.validators[event_type] = validator
        
    async def validate(self, event: Event) -> bool:
        validator = self.validators.get(event.type)
        if not validator:
            return True
            
        try:
            return await validator(event)
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
```

3. **Event Recovery**
```python
class EventRecovery:
    def __init__(self, event_stream: EventStream):
        self.event_stream = event_stream
        self.failed_events = []
        
    async def handle_failed_event(self, event: Event, error: Exception):
        self.failed_events.append({
            'event': event,
            'error': error,
            'timestamp': datetime.now()
        })
        
    async def retry_failed_events(self):
        for failed in self.failed_events[:]:
            try:
                await self.event_stream.emit(failed['event'])
                self.failed_events.remove(failed)
            except Exception as e:
                logger.error(f"Retry failed: {e}")
```

### 4. Memory Management Issues

#### Scenario
Memory leaks or inefficient memory usage.

#### Diagnosis
```python
# 1. Memory tracker
class MemoryTracker:
    def __init__(self):
        self.snapshots = []
        
    def take_snapshot(self):
        snapshot = {
            'timestamp': datetime.now(),
            'process': psutil.Process(),
            'memory': psutil.virtual_memory()
        }
        self.snapshots.append(snapshot)
        
    def analyze(self):
        return {
            'growth': self._analyze_growth(),
            'patterns': self._analyze_patterns(),
            'recommendations': self._get_recommendations()
        }
```

#### Common Causes and Solutions
1. **Resource Cleanup**
```python
class ManagedResource:
    def __init__(self):
        self.resources = weakref.WeakSet()
        
    async def acquire(self, resource: Any):
        self.resources.add(resource)
        return resource
        
    async def release(self, resource: Any):
        self.resources.remove(resource)
        await self._cleanup_resource(resource)
        
    async def _cleanup_resource(self, resource: Any):
        if hasattr(resource, 'close'):
            await resource.close()
```

2. **Memory Limits**
```python
class MemoryLimiter:
    def __init__(self, max_memory_mb: int):
        self.max_memory = max_memory_mb * 1024 * 1024
        
    async def check_memory(self):
        current = psutil.Process().memory_info().rss
        if current > self.max_memory:
            await self._reduce_memory()
            
    async def _reduce_memory(self):
        # Clear caches
        gc.collect()
        # Release resources
        # Compact memory
```

3. **Efficient Storage**
```python
class EfficientStorage:
    def __init__(self):
        self.data = {}
        self.index = {}
        
    async def store(self, key: str, value: Any):
        # Store compressed
        compressed = self._compress(value)
        self.data[key] = compressed
        
        # Update index
        self.index[key] = {
            'size': len(compressed),
            'timestamp': datetime.now()
        }
        
    def _compress(self, value: Any) -> bytes:
        # Implement compression
        return compressed_data
```

### 5. Configuration Issues

#### Scenario
Configuration not being applied correctly or missing settings.

#### Diagnosis
```python
# 1. Configuration validator
class ConfigValidator:
    def __init__(self):
        self.required = set()
        self.validators = {}
        
    def validate(self, config: dict) -> bool:
        # Check required fields
        for field in self.required:
            if field not in config:
                logger.error(f"Missing required field: {field}")
                return False
                
        # Run validators
        for field, validator in self.validators.items():
            if field in config and not validator(config[field]):
                logger.error(f"Invalid value for {field}")
                return False
                
        return True
```

#### Common Causes and Solutions
1. **Configuration Loading**
```python
class ConfigLoader:
    def __init__(self):
        self.sources = []
        self.cache = {}
        
    async def load(self) -> dict:
        config = {}
        
        # Load from each source
        for source in self.sources:
            try:
                source_config = await source.load()
                self._deep_update(config, source_config)
            except Exception as e:
                logger.error(f"Config load failed: {e}")
                
        return config
```

2. **Dynamic Configuration**
```python
class DynamicConfig:
    def __init__(self):
        self.config = {}
        self.watchers = {}
        
    async def update(self, updates: dict):
        # Apply updates
        self._deep_update(self.config, updates)
        
        # Notify watchers
        for path, watchers in self.watchers.items():
            if self._path_updated(path, updates):
                value = self._get_path(self.config, path)
                for watcher in watchers:
                    await watcher(value)
```

3. **Configuration Versioning**
```python
class VersionedConfig:
    def __init__(self):
        self.versions = []
        self.current = None
        
    async def update(self, config: dict):
        # Create new version
        version = {
            'config': config,
            'timestamp': datetime.now(),
            'version': len(self.versions) + 1
        }
        
        self.versions.append(version)
        self.current = version
        
    async def rollback(self, version: int):
        if 0 <= version < len(self.versions):
            self.current = self.versions[version]
```

Remember:
- Use debugging tools
- Check logs thoroughly
- Monitor system state
- Test changes carefully
- Document solutions
- Share knowledge