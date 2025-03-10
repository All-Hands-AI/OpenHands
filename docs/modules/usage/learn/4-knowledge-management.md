# OpenHands Knowledge Management and Self-Improvement Guide

OpenHands implements its memory system and knowledge extraction capabilities.

## OpenHands Knowledge Management Overview

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


### 1. Memory Architecture
```plaintext
OpenHands Memory System
│
├── Short-Term Memory (Event History)
│   ├── Active Context
│   │   - Current conversation state
│   │   - Recent events
│   │   - Active preferences
│   │
│   └── Event Filtering
│       - Important event retention
│       - Noise reduction
│       - Context window management
│
├── Memory Condensation
│   ├── LLM Summarization
│   │   - Event chunk summarization
│   │   - Context compression
│   │   - Key information extraction
│   │
│   └── Condensation Strategies
│       - Amortized forgetting
│       - Attention-based
│       - Observation masking
│
└── Long-Term Memory (Vector Store)
    ├── Persistent Storage
    │   - ChromaDB backend
    │   - Session-based organization
    │   - Event embeddings
    │
    └── Knowledge Retrieval
        - Semantic search
        - Relevance scoring
        - Context matching
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



#### Event Storage and Retrieval
```python

# File: openhands/events/stream.py

class EventStream:
    """Manages current conversation context"""
    
    def __init__(self, sid: str, file_store: FileStore):
        self.sid = sid
        self.file_store = file_store
        self.subscribers = {}
        self.history = []
        
    async def emit(self, event: Event):
        """Add event to history and notify subscribers"""
        # Store event
        self.history.append(event)
        
        # Notify subscribers
        for subscriber in self.subscribers:
            try:
                await subscriber.handle_event(event)
            except Exception as e:
                logger.error(f"Subscriber error: {e}")



# File: openhands/memory/memory.py

class LongTermMemory:
    """Persistent knowledge storage using vector database"""
    
    def __init__(
        self,
        llm_config: LLMConfig,
        agent_config: AgentConfig,
        event_stream: EventStream
    ):
        # Initialize ChromaDB
        self.db = chromadb.PersistentClient(
            path=f'./cache/sessions/{event_stream.sid}/memory'
        )
        self.collection = self.db.get_or_create_collection(
            name='memories'
        )
        
        # Setup vector store
        self.vector_store = ChromaVectorStore(
            chroma_collection=self.collection
        )
        
        # Initialize embedding model
        self.embed_model = EmbeddingsLoader.get_embedding_model(
            llm_config.embedding_model,
            llm_config
        )
        
    def add_event(self, event: Event):
        """Store event in long-term memory"""
        # Convert event to storable format
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
        
        # Store in vector database
        self._add_document(doc)
        
    def search(self, query: str, k: int = 10) -> list[str]:
        """Search through memory"""
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=k
        )
        return [r.get_text() for r in retriever.retrieve(query)]
```


## Cross-Session Knowledge Sharing

OpenHands implements cross-session knowledge sharing through:

1. **Persistent Storage**
```python
# Knowledge is stored in ChromaDB at:
f'./cache/sessions/{session_id}/memory'

# This allows:
- Session-specific storage
- Persistent across restarts
- Vector-based retrieval
```

2. **Knowledge Retrieval**
```python
class LongTermMemory:
    def search(self, query: str, k: int = 10) -> list[str]:
        """Retrieve relevant knowledge"""
        # Create retriever
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=k
        )
        
        # Search for similar content
        results = retriever.retrieve(query)
        
        # Return matched documents
        return [r.get_text() for r in results]
```

3. **Event Processing**
```python
class EventStream:
    async def process_event(self, event: Event):
        """Process and store events"""
        # Add to history
        self.history.append(event)
        
        # Store in long-term memory
        if self.memory:
            await self.memory.add_event(event)
            
        # Notify subscribers
        await self._notify_subscribers(event)
```




