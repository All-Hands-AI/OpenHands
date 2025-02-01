# OpenHands Practical Modification Guide

This guide provides practical examples of common system modifications and development scenarios in OpenHands.

## Common Modification Scenarios

### 1. Modifying Agent Behavior

#### Example: Adding Custom Processing Logic
```python
# Location: openhands/agenthub/custom_agent/agent.py

from openhands.controller.agent import Agent
from openhands.events import Event, EventSource
from openhands.events.action import Action

class CustomProcessingAgent(Agent):
    """Agent with custom processing logic"""
    
    def __init__(self, llm: LLM, config: Config):
        super().__init__(llm, config)
        self.processing_state = {}
        
    async def step(self, state: State) -> Action:
        # 1. Get latest input
        latest_event = state.get_latest_input()
        if not latest_event:
            return Action(message="No input to process")
            
        # 2. Process with LLM
        llm_response = await self.llm.generate(
            prompt=self._create_prompt(latest_event),
            context=self._get_context(state)
        )
        
        # 3. Custom processing
        processed_result = await self._custom_processing(
            llm_response,
            state
        )
        
        # 4. Generate action
        return Action(
            message=processed_result,
            source=EventSource.AGENT,
            metadata={'processed': True}
        )
        
    async def _custom_processing(
        self,
        llm_response: str,
        state: State
    ) -> str:
        # Add your custom processing logic here
        # Example: Format response, add metadata, etc.
        return processed_result
        
    def _create_prompt(self, event: Event) -> str:
        # Create custom prompt
        return f"""
        Process this input: {event.message}
        Previous context: {self.processing_state}
        """
        
    def _get_context(self, state: State) -> dict:
        # Get relevant context
        return {
            'history': state.get_history(),
            'variables': state.get_variables(),
            'processing_state': self.processing_state
        }

# Register the agent
Agent.register("custom_processing", CustomProcessingAgent)
```

### 2. Adding Runtime Capability

#### Example: Custom File Processing
```python
# Location: openhands/runtime/impl/custom_runtime.py

from openhands.runtime.base import Runtime
from openhands.events.action import Action
from openhands.events.observation import Observation

class CustomFileProcessor(Runtime):
    """Runtime with custom file processing"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.processors = self._initialize_processors()
        
    def _initialize_processors(self) -> dict:
        return {
            'process_csv': self._process_csv,
            'process_json': self._process_json,
            'process_yaml': self._process_yaml
        }
        
    async def execute(self, action: Action) -> Observation:
        """Execute custom action"""
        # 1. Check if action is supported
        if action.type not in self.processors:
            return await super().execute(action)
            
        # 2. Get processor
        processor = self.processors[action.type]
        
        # 3. Process file
        try:
            result = await processor(action.data)
            return Observation(
                content=result,
                metadata={'processed': True}
            )
        except Exception as e:
            return ErrorObservation(str(e))
            
    async def _process_csv(self, data: dict) -> dict:
        # Implement CSV processing
        file_path = data['file_path']
        options = data.get('options', {})
        # Process CSV file
        return result
        
    async def _process_json(self, data: dict) -> dict:
        # Implement JSON processing
        return result
        
    async def _process_yaml(self, data: dict) -> dict:
        # Implement YAML processing
        return result
```

### 3. Extending Event System

#### Example: Custom Event Processing
```python
# Location: openhands/events/custom_processor.py

from openhands.events import Event, EventStream
from openhands.events.event import EventSource

class CustomEventProcessor:
    """Custom event processing system"""
    
    def __init__(self, event_stream: EventStream):
        self.event_stream = event_stream
        self.processors = self._setup_processors()
        
    def _setup_processors(self) -> dict:
        return {
            'user_input': self._process_user_input,
            'agent_response': self._process_agent_response,
            'system_event': self._process_system_event
        }
        
    async def process_event(self, event: Event):
        """Process event with custom logic"""
        # 1. Determine event type
        event_type = self._get_event_type(event)
        
        # 2. Get processor
        processor = self.processors.get(event_type)
        if not processor:
            return
            
        # 3. Process event
        try:
            processed_event = await processor(event)
            
            # 4. Emit processed event
            if processed_event:
                await self.event_stream.emit(
                    processed_event,
                    source=EventSource.SYSTEM
                )
        except Exception as e:
            logger.error(f"Event processing error: {e}")
            
    async def _process_user_input(self, event: Event) -> Event:
        # Process user input
        # Example: Validate, transform, enhance
        return processed_event
        
    async def _process_agent_response(self, event: Event) -> Event:
        # Process agent response
        # Example: Format, validate, log
        return processed_event
        
    async def _process_system_event(self, event: Event) -> Event:
        # Process system event
        # Example: Monitor, alert, respond
        return processed_event
```

### 4. Adding Custom Memory System

#### Example: Enhanced Memory Management
```python
# Location: openhands/memory/enhanced_memory.py

from openhands.memory import Memory
from typing import Optional, List

class EnhancedMemory(Memory):
    """Enhanced memory system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.indexes = {}
        self.cache = {}
        
    async def store(
        self,
        key: str,
        value: Any,
        metadata: Optional[dict] = None
    ):
        """Store with enhanced features"""
        # 1. Prepare data
        storage_data = {
            'value': value,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }
        
        # 2. Store data
        await super().store(key, storage_data)
        
        # 3. Update indexes
        await self._update_indexes(key, storage_data)
        
        # 4. Update cache
        self._update_cache(key, storage_data)
        
    async def retrieve(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """Retrieve with caching"""
        # 1. Check cache
        if key in self.cache:
            return self.cache[key]['value']
            
        # 2. Get from storage
        data = await super().retrieve(key, default)
        if data:
            # 3. Update cache
            self._update_cache(key, data)
            return data['value']
            
        return default
        
    async def search(
        self,
        query: dict
    ) -> List[dict]:
        """Search with indexes"""
        results = []
        
        # 1. Check indexes
        for key, data in self.indexes.items():
            if self._matches_query(data, query):
                # 2. Get full data
                full_data = await self.retrieve(key)
                if full_data:
                    results.append(full_data)
                    
        return results
        
    def _update_indexes(
        self,
        key: str,
        data: dict
    ):
        """Update search indexes"""
        self.indexes[key] = {
            'metadata': data['metadata'],
            'timestamp': data['timestamp']
        }
        
    def _update_cache(
        self,
        key: str,
        data: dict
    ):
        """Update memory cache"""
        self.cache[key] = {
            'value': data['value'],
            'timestamp': datetime.now()
        }
        
        # Clean old cache entries
        self._clean_cache()
        
    def _clean_cache(self):
        """Clean old cache entries"""
        now = datetime.now()
        expired = [
            key for key, data in self.cache.items()
            if (now - data['timestamp']).seconds > 3600
        ]
        for key in expired:
            del self.cache[key]
```

### 5. Customizing Configuration

#### Example: Dynamic Configuration
```python
# Location: openhands/core/config/dynamic_config.py

class DynamicConfig:
    """Dynamic configuration system"""
    
    def __init__(self):
        self.config = {}
        self.watchers = {}
        self.defaults = {}
        
    async def load(self, config_path: str):
        """Load configuration"""
        # 1. Load base config
        base_config = self._load_file(config_path)
        
        # 2. Apply environment overrides
        env_config = self._load_environment()
        
        # 3. Merge configurations
        self.config = self._merge_configs(
            self.defaults,
            base_config,
            env_config
        )
        
        # 4. Notify watchers
        await self._notify_watchers()
        
    def watch(
        self,
        path: str,
        callback: Callable
    ):
        """Watch configuration changes"""
        if path not in self.watchers:
            self.watchers[path] = []
        self.watchers[path].append(callback)
        
    def get(
        self,
        path: str,
        default: Any = None
    ) -> Any:
        """Get configuration value"""
        return self._get_path(self.config, path, default)
        
    def set(
        self,
        path: str,
        value: Any
    ):
        """Set configuration value"""
        self._set_path(self.config, path, value)
        
    async def _notify_watchers(self):
        """Notify configuration watchers"""
        for path, callbacks in self.watchers.items():
            value = self.get(path)
            for callback in callbacks:
                await callback(value)
```

## Common Development Tasks

### 1. Adding New Features
```python
# Steps for adding new features:

1. Identify Extension Point
   - Agent behavior
   - Runtime capability
   - Event processing
   - Memory system

2. Create Component
   - Inherit base class
   - Implement interface
   - Add custom logic

3. Register Component
   - Use registration system
   - Configure behavior
   - Add documentation

4. Test Integration
   - Unit tests
   - Integration tests
   - System tests
```

### 2. Modifying Behavior
```python
# Steps for modifying behavior:

1. Locate Component
   - Find relevant files
   - Understand current logic
   - Identify change points

2. Implement Changes
   - Modify logic
   - Add new methods
   - Update interfaces

3. Update Configuration
   - Add settings
   - Set defaults
   - Document options

4. Verify Changes
   - Test functionality
   - Check performance
   - Validate behavior
```

### 3. Debugging Issues
```python
# Steps for debugging:

1. Enable Debug Logging
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. Add Debug Points
   ```python
   logger.debug(f"Processing state: {state}")
   logger.debug(f"Event data: {event}")
   logger.debug(f"Action result: {result}")
   ```

3. Monitor Events
   ```python
   class EventMonitor:
       async def monitor(self, event: Event):
           logger.debug(f"Event: {event}")
   ```

4. Track State
   ```python
   class StateTracker:
       def track(self, state: State):
           logger.debug(f"State: {state}")
   ```
```

Remember:
- Keep modifications focused
- Follow existing patterns
- Add proper documentation
- Include tests
- Consider performance
- Handle errors properly