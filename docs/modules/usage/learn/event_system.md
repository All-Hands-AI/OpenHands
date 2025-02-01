# OpenHands Event System Guide

This guide provides a detailed explanation of OpenHands' event system, which is the core communication mechanism between different components.

## Table of Contents
1. [Event System Overview](#event-system-overview)
2. [Event Stream](#event-stream)
3. [Event Types](#event-types)
4. [Implementation Examples](#implementation-examples)
5. [Best Practices](#best-practices)

## Event System Overview

The event system in OpenHands is built around the concept of an `EventStream` that manages the flow of events between different components.

### Key Components

1. **Event Sources**
```python
class EventSource(str, Enum):
    AGENT = 'agent'
    USER = 'user'
    ENVIRONMENT = 'environment'
```

2. **Event Stream Subscribers**
```python
class EventStreamSubscriber(str, Enum):
    AGENT_CONTROLLER = 'agent_controller'
    SECURITY_ANALYZER = 'security_analyzer'
    RESOLVER = 'openhands_resolver'
    SERVER = 'server'
    RUNTIME = 'runtime'
    MAIN = 'main'
    TEST = 'test'
```

## Event Stream

The `EventStream` class is the central component that manages event flow:

```python
class EventStream:
    def __init__(self, sid: str, file_store: FileStore):
        self.sid = sid
        self.file_store = file_store
        self._subscribers = {}
        self._queue = queue.Queue[Event]()
        self._thread_pools = {}
        self._thread_loops = {}
        self._lock = threading.Lock()
        self.secrets = {}
        
        # Start queue processing thread
        self._queue_thread = threading.Thread(target=self._run_queue_loop)
        self._queue_thread.daemon = True
        self._queue_thread.start()
```

### Key Features

1. **Event Subscription**
```python
def subscribe(
    self,
    subscriber_id: EventStreamSubscriber,
    callback: Callable,
    callback_id: str
):
    """Subscribe to events with a callback"""
    initializer = partial(self._init_thread_loop, subscriber_id, callback_id)
    pool = ThreadPoolExecutor(max_workers=1, initializer=initializer)
    
    if subscriber_id not in self._subscribers:
        self._subscribers[subscriber_id] = {}
        self._thread_pools[subscriber_id] = {}
    
    self._subscribers[subscriber_id][callback_id] = callback
    self._thread_pools[subscriber_id][callback_id] = pool
```

2. **Event Publishing**
```python
def add_event(self, event: Event, source: EventSource):
    """Add a new event to the stream"""
    with self._lock:
        event._id = self._cur_id
        self._cur_id += 1
    
    event._timestamp = datetime.now().isoformat()
    event._source = source
    
    # Store event
    data = event_to_dict(event)
    data = self._replace_secrets(data)
    self.file_store.write(
        self._get_filename_for_id(event.id),
        json.dumps(data)
    )
    
    # Queue for processing
    self._queue.put(event)
```

3. **Event Retrieval**
```python
def get_events(
    self,
    start_id: int = 0,
    end_id: int | None = None,
    reverse: bool = False,
    filter_out_type: tuple[type[Event], ...] | None = None,
    filter_hidden=False,
) -> Iterable[Event]:
    """Retrieve events with filtering options"""
    def should_filter(event: Event):
        if filter_hidden and hasattr(event, 'hidden') and event.hidden:
            return True
        if filter_out_type and isinstance(event, filter_out_type):
            return True
        return False
    
    event_id = start_id
    while should_continue():
        if end_id is not None and event_id > end_id:
            break
        try:
            event = self.get_event(event_id)
            if not should_filter(event):
                yield event
        except FileNotFoundError:
            break
        event_id += 1
```

## Implementation Examples

### 1. Custom Event Handler

```python
from openhands.events import Event, EventStream, EventStreamSubscriber
from openhands.events.event import EventSource

class CustomEventHandler:
    def __init__(self, event_stream: EventStream):
        self.event_stream = event_stream
        self.event_stream.subscribe(
            EventStreamSubscriber.MAIN,
            self.handle_event,
            "custom_handler"
        )
    
    def handle_event(self, event: Event):
        """Handle incoming events"""
        try:
            if event.source == EventSource.USER:
                self._handle_user_event(event)
            elif event.source == EventSource.AGENT:
                self._handle_agent_event(event)
        except Exception as e:
            logger.error(f"Error handling event: {e}")
    
    def _handle_user_event(self, event: Event):
        # Process user event
        response_event = Event(
            message="Processed user input",
            source=EventSource.ENVIRONMENT
        )
        self.event_stream.add_event(response_event, EventSource.ENVIRONMENT)
    
    def _handle_agent_event(self, event: Event):
        # Process agent event
        response_event = Event(
            message="Processed agent action",
            source=EventSource.ENVIRONMENT
        )
        self.event_stream.add_event(response_event, EventSource.ENVIRONMENT)
```

### 2. Event Filtering System

```python
class EventFilter:
    def __init__(self, event_stream: EventStream):
        self.event_stream = event_stream
    
    def get_filtered_events(
        self,
        query: str | None = None,
        source: EventSource | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        event_types: tuple[type[Event], ...] | None = None
    ) -> list[Event]:
        """Get events matching specific criteria"""
        return self.event_stream.get_matching_events(
            query=query,
            source=source.value if source else None,
            start_date=start_date,
            end_date=end_date,
            event_types=event_types
        )
    
    def get_user_events(self) -> list[Event]:
        """Get all user events"""
        return list(self.event_stream.filtered_events_by_source(
            EventSource.USER
        ))
    
    def get_agent_events(self) -> list[Event]:
        """Get all agent events"""
        return list(self.event_stream.filtered_events_by_source(
            EventSource.AGENT
        ))
```

### 3. Event Monitoring System

```python
class EventMonitor:
    def __init__(self, event_stream: EventStream):
        self.event_stream = event_stream
        self.stats = {
            "user_events": 0,
            "agent_events": 0,
            "environment_events": 0
        }
        self.event_stream.subscribe(
            EventStreamSubscriber.MAIN,
            self.monitor_event,
            "event_monitor"
        )
    
    def monitor_event(self, event: Event):
        """Monitor and collect statistics about events"""
        if event.source == EventSource.USER:
            self.stats["user_events"] += 1
        elif event.source == EventSource.AGENT:
            self.stats["agent_events"] += 1
        elif event.source == EventSource.ENVIRONMENT:
            self.stats["environment_events"] += 1
        
        self._check_thresholds()
    
    def _check_thresholds(self):
        """Check if any event type exceeds thresholds"""
        for event_type, count in self.stats.items():
            if count > 1000:
                logger.warning(f"High event count for {event_type}: {count}")
```

## Best Practices

### 1. Event Handling

1. **Thread Safety**
```python
class ThreadSafeEventHandler:
    def __init__(self):
        self._lock = threading.Lock()
        self._event_cache = {}
    
    def handle_event(self, event: Event):
        with self._lock:
            # Process event safely
            self._process_event(event)
    
    def _process_event(self, event: Event):
        # Safe event processing
        event_id = str(event.id)
        if event_id not in self._event_cache:
            self._event_cache[event_id] = event
```

2. **Error Recovery**
```python
class ResilientEventHandler:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
    
    async def handle_event_with_retry(self, event: Event):
        retries = 0
        while retries < self.max_retries:
            try:
                await self._process_event(event)
                break
            except Exception as e:
                retries += 1
                if retries == self.max_retries:
                    logger.error(f"Failed to process event after {retries} retries: {e}")
                    raise
                await asyncio.sleep(1 * retries)  # Exponential backoff
```

### 2. Event Stream Management

1. **Resource Management**
```python
class ManagedEventStream:
    def __init__(self, event_stream: EventStream):
        self.event_stream = event_stream
        self._subscribers = set()
    
    def add_subscriber(self, subscriber_id: str, callback: Callable):
        self._subscribers.add(subscriber_id)
        self.event_stream.subscribe(
            subscriber_id,
            callback,
            f"managed_{subscriber_id}"
        )
    
    def cleanup(self):
        """Clean up all subscribers"""
        for subscriber_id in self._subscribers:
            try:
                self.event_stream.unsubscribe(
                    subscriber_id,
                    f"managed_{subscriber_id}"
                )
            except Exception as e:
                logger.error(f"Error cleaning up subscriber {subscriber_id}: {e}")
```

2. **Event Batching**
```python
class EventBatcher:
    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size
        self.current_batch = []
    
    def add_to_batch(self, event: Event):
        self.current_batch.append(event)
        if len(self.current_batch) >= self.batch_size:
            self._process_batch()
    
    def _process_batch(self):
        try:
            # Process events in batch
            for event in self.current_batch:
                # Process event
                pass
            self.current_batch = []
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
```

### 3. Performance Optimization

1. **Event Caching**
```python
class CachedEventHandler:
    def __init__(self, cache_size: int = 1000):
        self.cache = {}
        self.cache_size = cache_size
        self._lru = []
    
    def get_event(self, event_id: int) -> Optional[Event]:
        if event_id in self.cache:
            self._update_lru(event_id)
            return self.cache[event_id]
        return None
    
    def add_event(self, event: Event):
        if len(self.cache) >= self.cache_size:
            self._evict_oldest()
        self.cache[event.id] = event
        self._update_lru(event.id)
    
    def _update_lru(self, event_id: int):
        if event_id in self._lru:
            self._lru.remove(event_id)
        self._lru.append(event_id)
    
    def _evict_oldest(self):
        if self._lru:
            oldest = self._lru.pop(0)
            del self.cache[oldest]
```

2. **Event Filtering Optimization**
```python
class OptimizedEventFilter:
    def __init__(self):
        self.index = {}
    
    def index_event(self, event: Event):
        """Index event for faster searching"""
        # Index by source
        if event.source not in self.index:
            self.index[event.source] = []
        self.index[event.source].append(event)
        
        # Index by timestamp
        timestamp = event.timestamp[:10]  # YYYY-MM-DD
        if timestamp not in self.index:
            self.index[timestamp] = []
        self.index[timestamp].append(event)
    
    def get_events_by_source(self, source: EventSource) -> list[Event]:
        """Fast retrieval by source"""
        return self.index.get(source, [])
    
    def get_events_by_date(self, date: str) -> list[Event]:
        """Fast retrieval by date"""
        return self.index.get(date, [])
```

Remember to:
- Handle events asynchronously when possible
- Implement proper error handling
- Use appropriate caching strategies
- Monitor event system performance
- Clean up resources properly