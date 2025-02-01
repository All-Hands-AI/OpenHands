# OpenHands Runtime and Memory Systems

This guide provides a deep dive into OpenHands' runtime and memory systems, explaining how they work and how to extend them.

## Table of Contents
1. [Runtime System](#runtime-system)
2. [Memory System](#memory-system)
3. [Implementation Examples](#implementation-examples)
4. [Best Practices](#best-practices)

## Runtime System

The runtime system is responsible for executing actions and managing the environment where agents operate.

### Runtime Base Class

The core of the runtime system is the `Runtime` class:

```python
from openhands.runtime.base import Runtime
from openhands.events import EventStream, Event
from openhands.events.action import Action
from openhands.events.observation import Observation

class Runtime:
    def __init__(
        self,
        config: AppConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = False,
    ):
        self.sid = sid
        self.event_stream = event_stream
        self.plugins = plugins or []
        self.config = config
        # ... initialization code ...
```

### Key Runtime Components

1. **Action Execution**
```python
def run_action(self, action: Action) -> Observation:
    """Execute an action and return observation"""
    if not action.runnable:
        return NullObservation('')
    
    action_type = action.action
    if action_type not in ACTION_TYPE_TO_CLASS:
        return ErrorObservation(f'Action {action_type} does not exist.')
    
    if not hasattr(self, action_type):
        return ErrorObservation(
            f'Action {action_type} is not supported in current runtime.'
        )
    
    observation = getattr(self, action_type)(action)
    return observation
```

2. **Environment Management**
```python
def add_env_vars(self, env_vars: dict[str, str]) -> None:
    """Add environment variables to both IPython and Bash"""
    # Add to IPython if Jupyter plugin is present
    if any(isinstance(plugin, JupyterRequirement) for plugin in self.plugins):
        code = 'import os\n'
        for key, value in env_vars.items():
            code += f'os.environ["{key}"] = {json.dumps(value)}\n'
        self.run_ipython(IPythonRunCellAction(code))
    
    # Add to Bash shell
    cmd = ''
    for key, value in env_vars.items():
        cmd += f'export {key}={json.dumps(value)}; '
    if cmd:
        self.run(CmdRunAction(cmd.strip()))
```

### Implementing Custom Actions

To add new action types:

1. Define the action class:
```python
from dataclasses import dataclass
from openhands.events.action import Action

@dataclass
class CustomAction(Action):
    action: str = "custom_action"
    data: dict
    runnable: bool = True
```

2. Implement the action handler in your runtime:
```python
class CustomRuntime(Runtime):
    def custom_action(self, action: CustomAction) -> Observation:
        try:
            # Process the action
            result = self._process_custom_action(action.data)
            return Observation(content=result)
        except Exception as e:
            return ErrorObservation(str(e))
    
    def _process_custom_action(self, data: dict) -> str:
        # Implement custom processing
        return f"Processed: {data}"
```

## Memory System

The memory system provides long-term storage and retrieval capabilities using vector embeddings.

### Long-Term Memory

The `LongTermMemory` class manages persistent storage:

```python
class LongTermMemory:
    def __init__(
        self,
        llm_config: LLMConfig,
        agent_config: AgentConfig,
        event_stream: EventStream,
    ):
        # Initialize ChromaDB
        db = chromadb.PersistentClient(
            path=f'./cache/sessions/{event_stream.sid}/memory',
        )
        self.collection = db.get_or_create_collection(name='memories')
        
        # Setup vector store
        vector_store = ChromaVectorStore(chroma_collection=self.collection)
        
        # Initialize embedding model
        self.embed_model = EmbeddingsLoader.get_embedding_model(
            llm_config.embedding_model,
            llm_config
        )
        
        # Create vector index
        self.index = VectorStoreIndex.from_vector_store(
            vector_store,
            self.embed_model
        )
```

### Memory Operations

1. **Adding Events**
```python
def add_event(self, event: Event):
    """Add event to long-term memory"""
    # Convert event to memory format
    event_data = event_to_memory(event, -1)
    
    # Create document
    doc = Document(
        text=json.dumps(event_data),
        doc_id=str(self.thought_idx),
        extra_info={
            'type': event_type,
            'id': event_id,
            'idx': self.thought_idx,
        },
    )
    self._add_document(doc)
```

2. **Searching Memory**
```python
def search(self, query: str, k: int = 10) -> list[str]:
    """Search through memory"""
    retriever = VectorIndexRetriever(
        index=self.index,
        similarity_top_k=k,
    )
    results = retriever.retrieve(query)
    return [r.get_text() for r in results]
```

## Implementation Examples

### 1. Custom Runtime with File Operations

```python
from openhands.runtime.base import Runtime
from openhands.events.action import FileReadAction, FileWriteAction
from openhands.events.observation import FileReadObservation, ErrorObservation

class FileSystemRuntime(Runtime):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_cache = {}
    
    def read(self, action: FileReadAction) -> Observation:
        try:
            with open(action.path, 'r') as f:
                content = f.read()
            self.file_cache[action.path] = content
            return FileReadObservation(content=content)
        except Exception as e:
            return ErrorObservation(str(e))
    
    def write(self, action: FileWriteAction) -> Observation:
        try:
            with open(action.path, 'w') as f:
                f.write(action.content)
            self.file_cache[action.path] = action.content
            return Observation("File written successfully")
        except Exception as e:
            return ErrorObservation(str(e))
```

### 2. Custom Memory System

```python
from openhands.memory.memory import LongTermMemory
from typing import Optional

class EnhancedMemory(LongTermMemory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recent_cache = []
        self.max_cache_size = 100
    
    def add_event(self, event: Event):
        # Add to vector store
        super().add_event(event)
        
        # Add to recent cache
        self.recent_cache.append(event)
        if len(self.recent_cache) > self.max_cache_size:
            self.recent_cache.pop(0)
    
    def search_recent(self, query: str, k: int = 5) -> list[Event]:
        """Search only recent events"""
        # Simple text matching for recent events
        matches = []
        for event in reversed(self.recent_cache):
            if query.lower() in str(event).lower():
                matches.append(event)
                if len(matches) >= k:
                    break
        return matches
    
    def get_context(self, query: str) -> dict:
        """Get combined context from recent and long-term memory"""
        recent = self.search_recent(query)
        longterm = self.search(query)
        
        return {
            "recent_context": recent,
            "historical_context": longterm
        }
```

## Best Practices

### 1. Runtime Development

1. **Resource Management**
   ```python
   class SafeRuntime(Runtime):
       def __init__(self, *args, **kwargs):
           super().__init__(*args, **kwargs)
           self.resources = set()
       
       def acquire_resource(self, resource_id: str):
           if resource_id in self.resources:
               raise RuntimeError(f"Resource {resource_id} already in use")
           self.resources.add(resource_id)
       
       def release_resource(self, resource_id: str):
           self.resources.remove(resource_id)
       
       def __exit__(self, *args):
           # Clean up resources
           self.resources.clear()
           super().__exit__(*args)
   ```

2. **Error Handling**
   ```python
   def safe_execute(self, action: Action) -> Observation:
       try:
           self.acquire_resource(action.resource_id)
           result = self.run_action(action)
           return result
       except Exception as e:
           return ErrorObservation(str(e))
       finally:
           self.release_resource(action.resource_id)
   ```

### 2. Memory Management

1. **Efficient Storage**
   ```python
   def optimize_storage(self, event: Event) -> Optional[Document]:
       # Skip storing debug or temporary events
       if event.is_debug or event.is_temporary:
           return None
       
       # Compress large content
       if len(str(event)) > 1000:
           return self._create_compressed_document(event)
       
       return self._create_standard_document(event)
   ```

2. **Memory Cleanup**
   ```python
   def cleanup_old_memories(self, days_old: int = 30):
       """Remove memories older than specified days"""
       cutoff = datetime.now() - timedelta(days=days_old)
       
       # Get all documents
       docs = self.collection.get()
       
       # Filter and remove old documents
       for doc in docs:
           if doc.timestamp < cutoff:
               self.collection.delete(doc.id)
   ```

### 3. Performance Optimization

1. **Batch Processing**
   ```python
   def batch_process_events(self, events: list[Event]):
       """Process multiple events efficiently"""
       documents = []
       for event in events:
           doc = self.optimize_storage(event)
           if doc:
               documents.append(doc)
       
       if documents:
           self.index.insert_nodes(self.create_nodes(documents))
   ```

2. **Caching**
   ```python
   class CachedRuntime(Runtime):
       def __init__(self, *args, **kwargs):
           super().__init__(*args, **kwargs)
           self.cache = {}
           self.cache_ttl = 300  # 5 minutes
       
       def get_cached_result(self, action: Action) -> Optional[Observation]:
           cache_key = str(action)
           if cache_key in self.cache:
               result, timestamp = self.cache[cache_key]
               if time.time() - timestamp < self.cache_ttl:
                   return result
           return None
       
       def cache_result(self, action: Action, result: Observation):
           cache_key = str(action)
           self.cache[cache_key] = (result, time.time())
   ```

Remember to:
- Implement proper cleanup in runtime destructors
- Handle resource limits in memory systems
- Implement proper error handling and recovery
- Use appropriate caching strategies
- Monitor performance metrics