"""
Base classes for the Perception Layer (L1)
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of perception events"""

    # Git events
    GIT_COMMIT = "git_commit"
    GIT_BRANCH_CREATED = "git_branch_created"
    GIT_BRANCH_DELETED = "git_branch_deleted"
    GIT_TAG_CREATED = "git_tag_created"

    # GitHub events
    GITHUB_ISSUE_OPENED = "github_issue_opened"
    GITHUB_ISSUE_CLOSED = "github_issue_closed"
    GITHUB_ISSUE_COMMENTED = "github_issue_commented"
    GITHUB_PR_OPENED = "github_pr_opened"
    GITHUB_PR_MERGED = "github_pr_merged"
    GITHUB_PR_COMMENTED = "github_pr_commented"
    GITHUB_MENTION = "github_mention"

    # File system events
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"

    # Health events
    TEST_FAILED = "test_failed"
    TEST_PASSED = "test_passed"
    BUILD_FAILED = "build_failed"
    BUILD_SUCCEEDED = "build_succeeded"
    DEPENDENCY_OUTDATED = "dependency_outdated"
    SECURITY_VULNERABILITY = "security_vulnerability"

    # System events
    SCHEDULED_PULSE = "scheduled_pulse"
    WEBHOOK_RECEIVED = "webhook_received"
    MANUAL_TRIGGER = "manual_trigger"


class EventPriority(Enum):
    """Priority levels for perception events"""
    CRITICAL = 1    # Immediate action required
    HIGH = 2        # Should act soon
    MEDIUM = 3      # Normal priority
    LOW = 4         # Can wait
    INFO = 5        # Informational only


@dataclass
class PerceptionEvent:
    """
    An event perceived by the system

    This represents something the system "senses" from its environment.
    """
    event_type: EventType
    priority: EventPriority
    timestamp: datetime
    source: str  # Which monitor detected this
    data: Dict[str, Any]

    # Auto-calculated fields
    id: str = field(default_factory=lambda: f"evt_{datetime.now().timestamp()}")
    processed: bool = False
    actions_taken: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for storage"""
        return {
            'id': self.id,
            'event_type': self.event_type.value,
            'priority': self.priority.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'data': self.data,
            'processed': self.processed,
            'actions_taken': self.actions_taken,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerceptionEvent':
        """Deserialize from dict"""
        return cls(
            id=data['id'],
            event_type=EventType(data['event_type']),
            priority=EventPriority(data['priority']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            source=data['source'],
            data=data['data'],
            processed=data['processed'],
            actions_taken=data['actions_taken'],
        )


class BaseMonitor(ABC):
    """
    Base class for all perception monitors

    Each monitor is responsible for watching a specific aspect of the environment.
    """

    def __init__(self, name: str, check_interval: int = 60):
        """
        Args:
            name: Name of this monitor
            check_interval: How often to check (seconds)
        """
        self.name = name
        self.check_interval = check_interval
        self.running = False
        self._task: Optional[asyncio.Task] = None

    @abstractmethod
    async def check(self) -> List[PerceptionEvent]:
        """
        Check for new events

        Returns:
            List of new events detected
        """
        pass

    async def start(self):
        """Start monitoring"""
        if self.running:
            logger.warning(f"Monitor {self.name} already running")
            return

        self.running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Monitor {self.name} started")

    async def stop(self):
        """Stop monitoring"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"Monitor {self.name} stopped")

    async def _monitor_loop(self):
        """Internal monitoring loop"""
        while self.running:
            try:
                events = await self.check()
                if events:
                    logger.info(f"Monitor {self.name} detected {len(events)} events")
                    for event in events:
                        await self._handle_event(event)
            except Exception as e:
                logger.error(f"Error in monitor {self.name}: {e}", exc_info=True)

            # Wait before next check
            await asyncio.sleep(self.check_interval)

    async def _handle_event(self, event: PerceptionEvent):
        """
        Handle a detected event

        Override this to customize event handling.
        """
        # Default: just log
        logger.info(f"Event detected: {event.event_type.value} (priority: {event.priority.name})")


class PerceptionLayer:
    """
    L1: Perception Layer

    Coordinates all monitors and provides a unified interface for perceived events.
    """

    def __init__(self):
        self.monitors: List[BaseMonitor] = []
        self.event_queue: asyncio.Queue[PerceptionEvent] = asyncio.Queue()
        self.running = False

    def register_monitor(self, monitor: BaseMonitor):
        """Register a new monitor"""
        self.monitors.append(monitor)
        logger.info(f"Registered monitor: {monitor.name}")

    async def start(self):
        """Start all monitors"""
        if self.running:
            logger.warning("Perception layer already running")
            return

        self.running = True

        # Start all monitors
        for monitor in self.monitors:
            await monitor.start()

        logger.info(f"Perception layer started with {len(self.monitors)} monitors")

    async def stop(self):
        """Stop all monitors"""
        self.running = False

        # Stop all monitors
        for monitor in self.monitors:
            await monitor.stop()

        logger.info("Perception layer stopped")

    async def get_next_event(self, timeout: Optional[float] = None) -> Optional[PerceptionEvent]:
        """
        Get the next event from the queue

        Args:
            timeout: Max time to wait (seconds), None = wait forever

        Returns:
            Next event, or None if timeout
        """
        try:
            if timeout:
                return await asyncio.wait_for(self.event_queue.get(), timeout=timeout)
            else:
                return await self.event_queue.get()
        except asyncio.TimeoutError:
            return None

    async def get_events_batch(self, max_events: int = 10, timeout: float = 1.0) -> List[PerceptionEvent]:
        """
        Get a batch of events

        Args:
            max_events: Maximum number of events to return
            timeout: Max time to wait for first event

        Returns:
            List of events (may be empty)
        """
        events = []

        # Wait for first event
        first_event = await self.get_next_event(timeout)
        if not first_event:
            return events

        events.append(first_event)

        # Get more events without blocking
        while len(events) < max_events:
            try:
                event = self.event_queue.get_nowait()
                events.append(event)
            except asyncio.QueueEmpty:
                break

        return events

    def emit_event(self, event: PerceptionEvent):
        """
        Emit an event to the queue

        Monitors should call this when they detect something.
        """
        try:
            self.event_queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning(f"Event queue full, dropping event: {event.event_type.value}")
