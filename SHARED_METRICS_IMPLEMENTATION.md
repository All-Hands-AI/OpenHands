# Shared Metrics System Implementation

## Overview

This implementation creates exactly one metrics class per conversation and shares it with every LLM object, ensuring thread-safe cost accumulation across all LLM operations within a conversation.

## Key Components

### 1. ConversationMetrics Class (`openhands/llm/conversation_metrics.py`)

- **Purpose**: Thread-safe metrics manager for a conversation
- **Features**:
  - Queue-based operation processing to handle concurrent access
  - Single Metrics instance per conversation
  - Thread-safe methods for adding costs, token usage, and response latencies
  - Automatic queue processing with locking mechanism

### 2. ThreadSafeMetrics Class (`openhands/llm/conversation_metrics.py`)

- **Purpose**: Thread-safe wrapper around the Metrics class
- **Features**:
  - Provides same interface as Metrics class
  - Delegates operations to ConversationMetrics instance
  - Maintains compatibility with existing LLM code

### 3. State Integration (`openhands/controller/state/state.py`)

- **Added**: `conversation_metrics: ConversationMetrics | None = None` field
- **Purpose**: Store conversation metrics in the agent state for access by all components

## Implementation Flow

### 1. Conversation Creation

In `standalone_conversation_manager.py`:
```python
# Create conversation metrics instance
conversation_metrics = ConversationMetrics()

# Pass to session creation
session = Session(
    session_id=conversation_id,
    file_store=self.file_store,
    conversation_metrics=conversation_metrics,
    # ... other parameters
)
```

### 2. LLM Object Creation

All LLM objects now check for conversation_metrics and use ThreadSafeMetrics when available:

#### Draft Editor (`openhands/runtime/utils/edit.py`)
```python
if conversation_metrics:
    llm_metrics = ThreadSafeMetrics(
        conversation_metrics,
        model_name='draft_editor:' + draft_editor_config.model
    )
else:
    llm_metrics = Metrics(model_name='draft_editor:' + draft_editor_config.model)
```

#### Memory Condensers
All condenser implementations updated to accept `conversation_metrics` parameter:
- `LLMAttentionCondenser`
- `LLMSummarizingCondenser`
- `StructuredSummaryCondenser`
- `NoOpCondenser`
- `RecentEventsCondenser`
- `ObservationMaskingCondenser`
- `BrowserOutputCondenser`
- `AmortizedForgettingCondenser`
- `CondenserPipeline`

#### Title Generation (`openhands/utils/conversation_summary.py`)
```python
if conversation_metrics:
    llm_metrics = ThreadSafeMetrics(
        conversation_metrics,
        model_name='title_generator:' + llm_config.model
    )
else:
    llm_metrics = Metrics(model_name='title_generator:' + llm_config.model)
```

### 3. Agent Integration

#### CodeAct Agent (`openhands/agenthub/codeact_agent/codeact_agent.py`)
- Lazy condenser creation to access conversation_metrics from state
- `_get_condenser()` method creates condenser with conversation_metrics when available

#### Session Management
- `Session._create_llm()` uses conversation_metrics when available
- `AgentSession` stores and passes conversation_metrics to runtime creation
- State restoration preserves conversation_metrics

## Thread Safety Mechanism

### Queue-Based Operations
```python
class ConversationMetrics:
    def __init__(self):
        self._metrics = Metrics(model_name='conversation')
        self._operation_queue: queue.Queue[MetricsOperation] = queue.Queue()
        self._lock = threading.Lock()
        self._processing = False

    def _process_queue(self):
        # Thread-safe queue processing with locking
        with self._lock:
            if self._processing:
                return
            self._processing = True

        try:
            while True:
                try:
                    operation = self._operation_queue.get_nowait()
                    operation.apply(self._metrics)
                    self._operation_queue.task_done()
                except queue.Empty:
                    break
        finally:
            with self._lock:
                self._processing = False
```

### Operation Classes
- `AddCostOperation`: Queued cost additions
- `AddResponseLatencyOperation`: Queued latency additions
- `AddTokenUsageOperation`: Queued token usage additions

## Benefits

1. **Single Metrics Instance**: Exactly one metrics object per conversation
2. **Thread Safety**: Queue-based mechanism prevents race conditions
3. **Shared Accumulation**: All LLM objects contribute to same metrics
4. **Backward Compatibility**: Fallback to individual metrics when conversation_metrics not available
5. **Comprehensive Coverage**: Includes draft editor, memory condensers, and title generation
6. **Type Safety**: Proper type annotations and mypy compliance

## Testing

The implementation includes comprehensive testing for:
- Thread safety with multiple concurrent LLM operations
- Proper cost accumulation across different LLM objects
- Backward compatibility when conversation_metrics not available
- Integration with all condenser types
- State management and restoration

## Files Modified

### Core Implementation
- `openhands/llm/conversation_metrics.py` (new)
- `openhands/controller/state/state.py`

### Session Management
- `openhands/server/conversation_manager/standalone_conversation_manager.py`
- `openhands/server/session/session.py`
- `openhands/server/session/agent_session.py`

### Runtime Integration
- `openhands/runtime/base.py`
- `openhands/runtime/utils/edit.py`

### Memory Condensers
- `openhands/memory/condenser/condenser.py`
- `openhands/memory/condenser/impl/llm_attention_condenser.py`
- `openhands/memory/condenser/impl/llm_summarizing_condenser.py`
- `openhands/memory/condenser/impl/structured_summary_condenser.py`
- `openhands/memory/condenser/impl/no_op_condenser.py`
- `openhands/memory/condenser/impl/recent_events_condenser.py`
- `openhands/memory/condenser/impl/observation_masking_condenser.py`
- `openhands/memory/condenser/impl/browser_output_condenser.py`
- `openhands/memory/condenser/impl/amortized_forgetting_condenser.py`
- `openhands/memory/condenser/impl/pipeline.py`

### Agent Integration
- `openhands/agenthub/codeact_agent/codeact_agent.py`

### Utilities
- `openhands/utils/conversation_summary.py`

## Usage Example

```python
# Create conversation metrics
conversation_metrics = ConversationMetrics()

# Multiple LLM objects share the same metrics
draft_editor_metrics = ThreadSafeMetrics(conversation_metrics, 'draft_editor')
condenser_metrics = ThreadSafeMetrics(conversation_metrics, 'condenser')
title_gen_metrics = ThreadSafeMetrics(conversation_metrics, 'title_generator')

# All operations accumulate in the same conversation metrics
draft_editor_metrics.add_cost(0.01)
condenser_metrics.add_cost(0.02)
title_gen_metrics.add_cost(0.03)

# Total cost: 0.06
print(conversation_metrics.accumulated_cost)  # 0.06
```
