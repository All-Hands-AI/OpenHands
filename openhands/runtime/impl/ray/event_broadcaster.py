"""Ray-based distributed event broadcasting system."""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor

import ray

from openhands.events.event import Event, EventSource
from openhands.events.serialization.event import event_from_dict, event_to_dict
from openhands.events.stream import EventStreamSubscriber

logger = logging.getLogger(__name__)


@ray.remote
class RayEventBroadcaster:
    """Ray actor for distributed event broadcasting."""
    
    def __init__(self):
        """Initialize the Ray event broadcaster."""
        self.subscribers: Dict[str, Dict[str, Any]] = {}
        self.event_history: List[Dict[str, Any]] = []
        self.max_history = 1000  # Keep last 1000 events
        logger.info("RayEventBroadcaster initialized")
    
    def add_subscriber(self, subscriber_id: str, callback_id: str, worker_id: str = None) -> bool:
        """Add a subscriber to the event broadcasting system."""
        try:
            if subscriber_id not in self.subscribers:
                self.subscribers[subscriber_id] = {}
            
            self.subscribers[subscriber_id][callback_id] = {
                'worker_id': worker_id,
                'last_seen': time.time(),
                'event_count': 0
            }
            
            logger.info(f"Added subscriber {subscriber_id}/{callback_id} (worker: {worker_id})")
            return True
        except Exception as e:
            logger.error(f"Error adding subscriber {subscriber_id}/{callback_id}: {e}")
            return False
    
    def remove_subscriber(self, subscriber_id: str, callback_id: str) -> bool:
        """Remove a subscriber from the event broadcasting system."""
        try:
            if subscriber_id in self.subscribers and callback_id in self.subscribers[subscriber_id]:
                del self.subscribers[subscriber_id][callback_id]
                if not self.subscribers[subscriber_id]:
                    del self.subscribers[subscriber_id]
                logger.info(f"Removed subscriber {subscriber_id}/{callback_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing subscriber {subscriber_id}/{callback_id}: {e}")
            return False
    
    def broadcast_event(self, event_data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Broadcast an event to all subscribers."""
        try:
            # Add metadata
            event_data['broadcast_timestamp'] = time.time()
            event_data['broadcast_source'] = source
            
            # Store in history
            self.event_history.append(event_data.copy())
            if len(self.event_history) > self.max_history:
                self.event_history.pop(0)
            
            # Count subscribers that will receive this event
            total_subscribers = sum(len(callbacks) for callbacks in self.subscribers.values())
            
            # Update subscriber stats
            for subscriber_id, callbacks in self.subscribers.items():
                for callback_id, info in callbacks.items():
                    info['event_count'] += 1
                    info['last_seen'] = time.time()
            
            logger.debug(f"Broadcasted event to {total_subscribers} subscribers")
            
            return {
                'success': True,
                'subscribers_notified': total_subscribers,
                'event_id': event_data.get('id'),
                'timestamp': event_data['broadcast_timestamp']
            }
            
        except Exception as e:
            logger.error(f"Error broadcasting event: {e}")
            return {
                'success': False,
                'error': str(e),
                'subscribers_notified': 0
            }
    
    def get_subscriber_stats(self) -> Dict[str, Any]:
        """Get statistics about current subscribers."""
        stats = {
            'total_subscribers': 0,
            'subscribers_by_type': {},
            'active_workers': set(),
            'event_history_size': len(self.event_history),
            'subscriber_details': {}
        }
        
        for subscriber_id, callbacks in self.subscribers.items():
            subscriber_count = len(callbacks)
            stats['total_subscribers'] += subscriber_count
            stats['subscribers_by_type'][subscriber_id] = subscriber_count
            
            for callback_id, info in callbacks.items():
                if info['worker_id']:
                    stats['active_workers'].add(info['worker_id'])
                
                stats['subscriber_details'][f"{subscriber_id}/{callback_id}"] = {
                    'worker_id': info['worker_id'],
                    'event_count': info['event_count'],
                    'last_seen_ago': time.time() - info['last_seen']
                }
        
        stats['active_workers'] = list(stats['active_workers'])
        return stats
    
    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent events from the history."""
        return self.event_history[-limit:] if self.event_history else []
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for the broadcaster."""
        return {
            'status': 'healthy',
            'uptime': time.time(),
            'subscribers': len(self.subscribers),
            'events_in_history': len(self.event_history)
        }


class RayEventStream:
    """Ray-based distributed event streaming system."""
    
    def __init__(self, session_id: str, worker_pool=None):
        """Initialize Ray event stream.
        
        Args:
            session_id: Session identifier
            worker_pool: Optional worker pool for distributed callbacks
        """
        self.session_id = session_id
        self.worker_pool = worker_pool
        self.broadcaster = None
        self.subscribers: Dict[str, Dict[str, Callable]] = {}
        self.callback_executors: Dict[str, ThreadPoolExecutor] = {}
        self._initialized = False
        
        # Ray pub/sub topics
        self.event_topic = f"openhands_events_{session_id}"
        self.control_topic = f"openhands_control_{session_id}"
        
        logger.info(f"RayEventStream initialized for session {session_id}")
    
    async def initialize(self) -> None:
        """Initialize the Ray event broadcasting system."""
        try:
            if not ray.is_initialized():
                logger.warning("Ray not initialized, cannot start distributed event streaming")
                return
            
            # Create broadcaster actor
            self.broadcaster = RayEventBroadcaster.remote()
            
            # Start event subscription system
            await self._start_event_subscription()
            
            self._initialized = True
            logger.info(f"Ray event stream initialized for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ray event stream: {e}")
            raise
    
    async def _start_event_subscription(self) -> None:
        """Start Ray pub/sub subscription for events."""
        try:
            # In a full implementation, this would use Ray's pub/sub system
            # For now, we'll implement a polling-based approach with the broadcaster
            logger.info("Event subscription system started (broadcaster-based)")
        except Exception as e:
            logger.error(f"Failed to start event subscription: {e}")
            raise
    
    def subscribe(
        self, 
        subscriber_id: EventStreamSubscriber, 
        callback: Callable[[Event], None],
        callback_id: str,
        worker_id: Optional[str] = None
    ) -> None:
        """Subscribe to distributed events.
        
        Args:
            subscriber_id: Type of subscriber
            callback: Callback function to handle events
            callback_id: Unique identifier for this callback
            worker_id: Optional worker ID for distributed callbacks
        """
        try:
            if not self._initialized:
                logger.warning("RayEventStream not initialized, subscription may not work properly")
            
            if subscriber_id not in self.subscribers:
                self.subscribers[subscriber_id] = {}
                
            if callback_id in self.subscribers[subscriber_id]:
                raise ValueError(f"Callback ID {callback_id} already exists for subscriber {subscriber_id}")
            
            self.subscribers[subscriber_id][callback_id] = callback
            
            # Create thread executor for this callback
            executor_key = f"{subscriber_id}_{callback_id}"
            self.callback_executors[executor_key] = ThreadPoolExecutor(max_workers=1)
            
            # Register with Ray broadcaster
            if self.broadcaster:
                ray.get(self.broadcaster.add_subscriber.remote(subscriber_id, callback_id, worker_id))
            
            logger.info(f"Subscribed {subscriber_id}/{callback_id} to distributed events")
            
        except Exception as e:
            logger.error(f"Error subscribing {subscriber_id}/{callback_id}: {e}")
            raise
    
    def unsubscribe(self, subscriber_id: EventStreamSubscriber, callback_id: str) -> None:
        """Unsubscribe from distributed events."""
        try:
            if subscriber_id not in self.subscribers:
                logger.warning(f"Subscriber {subscriber_id} not found during unsubscribe")
                return
                
            if callback_id not in self.subscribers[subscriber_id]:
                logger.warning(f"Callback {callback_id} not found during unsubscribe")
                return
            
            # Clean up callback
            del self.subscribers[subscriber_id][callback_id]
            if not self.subscribers[subscriber_id]:
                del self.subscribers[subscriber_id]
            
            # Clean up thread executor
            executor_key = f"{subscriber_id}_{callback_id}"
            if executor_key in self.callback_executors:
                self.callback_executors[executor_key].shutdown(wait=True)
                del self.callback_executors[executor_key]
            
            # Remove from Ray broadcaster
            if self.broadcaster:
                ray.get(self.broadcaster.remove_subscriber.remote(subscriber_id, callback_id))
            
            logger.info(f"Unsubscribed {subscriber_id}/{callback_id} from distributed events")
            
        except Exception as e:
            logger.error(f"Error unsubscribing {subscriber_id}/{callback_id}: {e}")
    
    def add_event(self, event: Event, source: EventSource) -> None:
        """Add an event to the distributed stream."""
        try:
            if not self._initialized:
                logger.warning("RayEventStream not initialized, event may not be distributed")
                return
            
            # Convert event to dictionary for serialization
            event_data = event_to_dict(event)
            
            # Broadcast via Ray
            if self.broadcaster:
                result = ray.get(self.broadcaster.broadcast_event.remote(
                    event_data, 
                    str(source)
                ))
                
                if result.get('success'):
                    logger.debug(f"Event {event.id} broadcasted to {result['subscribers_notified']} subscribers")
                else:
                    logger.error(f"Failed to broadcast event: {result.get('error')}")
            
            # Process local callbacks
            self._process_local_callbacks(event)
            
        except Exception as e:
            logger.error(f"Error adding event to distributed stream: {e}")
    
    def _process_local_callbacks(self, event: Event) -> None:
        """Process callbacks for local subscribers."""
        for subscriber_id, callbacks in self.subscribers.items():
            for callback_id, callback in callbacks.items():
                executor_key = f"{subscriber_id}_{callback_id}"
                if executor_key in self.callback_executors:
                    executor = self.callback_executors[executor_key]
                    try:
                        executor.submit(callback, event)
                    except Exception as e:
                        logger.error(f"Error executing callback {subscriber_id}/{callback_id}: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get distributed event streaming statistics."""
        try:
            if not self.broadcaster:
                return {'error': 'Broadcaster not initialized'}
            
            stats = ray.get(self.broadcaster.get_subscriber_stats.remote())
            stats['session_id'] = self.session_id
            stats['local_subscribers'] = len(self.subscribers)
            stats['initialized'] = self._initialized
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting event stream stats: {e}")
            return {'error': str(e)}
    
    async def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent events from the distributed stream."""
        try:
            if not self.broadcaster:
                return []
            
            events = ray.get(self.broadcaster.get_recent_events.remote(limit))
            return events
            
        except Exception as e:
            logger.error(f"Error getting recent events: {e}")
            return []
    
    def close(self) -> None:
        """Close the distributed event stream."""
        try:
            # Shutdown all executors
            for executor in self.callback_executors.values():
                executor.shutdown(wait=True)
            self.callback_executors.clear()
            
            # Clear subscribers
            self.subscribers.clear()
            
            # Note: We don't shut down the broadcaster actor here as it might be shared
            # In a production system, you'd implement proper resource management
            
            self._initialized = False
            logger.info(f"Ray event stream closed for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error closing Ray event stream: {e}")