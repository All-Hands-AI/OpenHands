# OpenHands Memory System and Knowledge Extraction Tutorial

This tutorial explains how OpenHands actually implements its memory system and knowledge extraction capabilities, based on the real codebase.

## Memory System Overview

OpenHands implements a sophisticated memory and knowledge extraction system through three main components:

1. **Event Stream** (`openhands/events/stream.py`)
   - Handles real-time event processing
   - Maintains conversation history

2. **Condenser System** (`openhands/memory/condenser/`)
   - Extracts and summarizes knowledge from events
   - Multiple condensation strategies
   - LLM-based summarization

3. **Long-Term Memory** (`openhands/memory/memory.py`)
   - Vector-based knowledge storage
   - Cross-session persistence
   - Knowledge retrieval

## Knowledge Extraction System

The key to OpenHands' knowledge extraction is its Condenser system. Let's look at how it works:

### 1. Base Condenser System
```python
# File: openhands/memory/condenser/condenser.py

class Condenser(ABC):
    """Base condenser for knowledge extraction"""
    
    def __init__(self):
        self._metadata_batch: dict[str, Any] = {}
        
    @abstractmethod
    def condense(self, events: list[Event]) -> list[Event]:
        """Condense events into knowledge"""
        pass
        
    def condensed_history(self, state: State) -> list[Event]:
        """Process state history"""
        with self.metadata_batch(state):
            return self.condense(state.history)
            
    def add_metadata(self, key: str, value: Any):
        """Track condensation metadata"""
        self._metadata_batch[key] = value
```

### 2. LLM-Based Knowledge Extraction
```python
# File: openhands/memory/condenser/impl/llm_summarizing_condenser.py

class LLMSummarizingCondenser(Condenser):
    """Extracts knowledge using LLM summarization"""
    
    def __init__(self, llm: LLM):
        self.llm = llm
        super().__init__()
        
    def condense(self, events: list[Event]) -> list[Event]:
        # Convert events to text format
        events_text = '\n'.join(
            f'{e.timestamp}: {e.message}'
            for e in events
        )
        
        # Generate knowledge summary
        resp = self.llm.completion(
            messages=[{
                'content': f'Please summarize these events:\n{events_text}',
                'role': 'user'
            }]
        )
        
        # Create condensed knowledge event
        summary = resp.choices[0].message.content
        summary_event = AgentCondensationObservation(summary)
        
        # Track metrics
        self.add_metadata('response', resp.model_dump())
        self.add_metadata('metrics', self.llm.metrics.get())
        
        return [summary_event]
```

### 3. Rolling Knowledge Accumulation
```python
# File: openhands/memory/condenser/condenser.py

class RollingCondenser(Condenser, ABC):
    """Accumulates knowledge over time"""
    
    def __init__(self):
        self._condensation: list[Event] = []
        self._last_history_length: int = 0
        super().__init__()
        
    def condensed_history(self, state: State) -> list[Event]:
        # Get new events since last condensation
        new_events = state.history[self._last_history_length:]
        
        # Condense with previous knowledge
        with self.metadata_batch(state):
            results = self.condense(
                self._condensation + new_events
            )
        
        # Update condensation state
        self._condensation = results
        self._last_history_length = len(state.history)
        
        return results
```

## Knowledge Storage and Retrieval

### 1. Vector-Based Storage
```python
# File: openhands/memory/memory.py

class LongTermMemory:
    """Stores extracted knowledge"""
    
    def __init__(self, llm_config: LLMConfig, agent_config: AgentConfig, event_stream: EventStream):
        # Initialize vector store
        self.db = chromadb.PersistentClient(
            path=f'./cache/sessions/{event_stream.sid}/memory'
        )
        self.collection = self.db.get_or_create_collection('memories')
        
        # Setup embeddings
        self.embed_model = EmbeddingsLoader.get_embedding_model(
            llm_config.embedding_model,
            llm_config
        )
        
    def add_event(self, event: Event):
        """Store event knowledge"""
        # Convert to storable format
        event_data = event_to_memory(event, -1)
        
        # Create document
        doc = Document(
            text=json.dumps(event_data),
            doc_id=str(self.thought_idx),
            extra_info={
                'type': event_type,
                'id': event_id,
                'idx': self.thought_idx
            }
        )
        
        # Store with vector embedding
        self._add_document(doc)
```

## Knowledge Flow in OpenHands

1. **Event Processing**
   ```plaintext
   User Input/System Event
          ↓
   Event Stream
          ↓
   Condenser System (Knowledge Extraction)
          ↓
   Long-Term Memory (Storage)
   ```

2. **Knowledge Retrieval**
   ```plaintext
   Query/Context
          ↓
   Vector Search
          ↓
   Relevant Knowledge
          ↓
   Agent Processing
   ```

3. **Knowledge Accumulation**
   ```plaintext
   New Events
          ↓
   Rolling Condenser
          ↓
   Updated Knowledge Summary
          ↓
   Vector Storage Update
   ```

## Using the Knowledge System

### 1. Setting Up Condensers
```python
# Configure condenser
config = LLMSummarizingCondenserConfig(
    llm_config=llm_config
)

# Create condenser
condenser = LLMSummarizingCondenser.from_config(config)
```

### 2. Processing Events
```python
# In your agent
class YourAgent(Agent):
    async def step(self, state: State) -> Action:
        # Get condensed knowledge
        condensed = self.condenser.condensed_history(state)
        
        # Use in context
        context = {
            'history': condensed,
            'current_state': state
        }
        
        # Generate response
        response = await self.llm.generate(
            prompt=self._create_prompt(state),
            context=context
        )
        
        return self._create_action(response)
```

### 3. Accessing Stored Knowledge
```python
# Search knowledge
results = memory.search(
    query="relevant context",
    k=10  # number of results
)

# Use in processing
context = {
    'knowledge': results,
    'current_input': current_event
}
```

## Best Practices

1. **Knowledge Extraction**
   - Use appropriate condenser for your needs
   - Monitor condensation quality
   - Track metadata for debugging

2. **Storage Management**
   - Regular cleanup of old sessions
   - Monitor vector store size
   - Validate stored knowledge

3. **Performance**
   - Use batch processing when possible
   - Cache frequent queries
   - Monitor embedding performance

4. **Knowledge Quality**
   - Validate extracted knowledge
   - Update outdated information
   - Track knowledge confidence
