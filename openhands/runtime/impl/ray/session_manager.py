"""Session management for distributed Ray runtime execution."""

import asyncio
import time
import uuid
from enum import Enum
from typing import Any, Dict, Optional, Set
import logging

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """Session lifecycle states."""
    ACTIVE = "active"
    IDLE = "idle"
    MIGRATING = "migrating"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class SessionType(Enum):
    """Types of sessions that require state management."""
    EPHEMERAL = "ephemeral"  # No state persistence needed
    IPYTHON = "ipython"      # IPython kernel state
    FILE_CONTEXT = "file_context"  # File system context
    COMBINED = "combined"    # Multiple state types


class SessionInfo:
    """Information about a managed session."""
    
    def __init__(
        self,
        session_id: str,
        session_type: SessionType = SessionType.EPHEMERAL,
        worker_id: Optional[str] = None
    ):
        self.session_id = session_id
        self.session_type = session_type
        self.worker_id = worker_id
        self.state = SessionState.ACTIVE
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.access_count = 0
        self.metadata: Dict[str, Any] = {}
        
        # State-specific tracking
        self.ipython_kernel_id: Optional[str] = None
        self.working_directory: Optional[str] = None
        self.environment_variables: Dict[str, str] = {}
        self.open_files: Set[str] = set()
    
    def update_access(self):
        """Update last access time and increment counter."""
        self.last_accessed = time.time()
        self.access_count += 1
    
    def is_expired(self, timeout_seconds: float) -> bool:
        """Check if session has expired based on inactivity."""
        return (time.time() - self.last_accessed) > timeout_seconds
    
    def requires_state_persistence(self) -> bool:
        """Check if session requires state to be maintained."""
        return self.session_type in [SessionType.IPYTHON, SessionType.FILE_CONTEXT, SessionType.COMBINED]


class SessionManager:
    """Manages session lifecycle and state for distributed Ray runtime."""
    
    def __init__(
        self,
        default_timeout: float = 1800.0,  # 30 minutes
        cleanup_interval: float = 300.0,  # 5 minutes
        max_sessions: int = 100
    ):
        self.default_timeout = default_timeout
        self.cleanup_interval = cleanup_interval
        self.max_sessions = max_sessions
        
        self.sessions: Dict[str, SessionInfo] = {}
        self.worker_sessions: Dict[str, Set[str]] = {}  # worker_id -> session_ids
        
        self._cleanup_task: Optional[asyncio.Task] = None
        self._initialized = False
        
        logger.info("SessionManager initialized")
    
    async def initialize(self):
        """Initialize the session manager."""
        if self._initialized:
            return
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._initialized = True
        
        logger.info("SessionManager started")
    
    def create_session(
        self,
        session_type: SessionType = SessionType.EPHEMERAL,
        session_id: Optional[str] = None,
        worker_id: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> str:
        """Create a new session and return its ID."""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Check session limits
        if len(self.sessions) >= self.max_sessions:
            # Try to clean up expired sessions first
            self._cleanup_expired_sessions()
            
            if len(self.sessions) >= self.max_sessions:
                # Force cleanup of oldest idle sessions
                self._force_cleanup_oldest_sessions()
        
        # Create session info
        session_info = SessionInfo(session_id, session_type, worker_id)
        if timeout:
            session_info.metadata['timeout'] = timeout
        
        self.sessions[session_id] = session_info
        
        # Track by worker
        if worker_id:
            if worker_id not in self.worker_sessions:
                self.worker_sessions[worker_id] = set()
            self.worker_sessions[worker_id].add(session_id)
        
        logger.info(f"Created session {session_id} (type: {session_type.value}, worker: {worker_id})")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session information and update access time."""
        session_info = self.sessions.get(session_id)
        if session_info:
            session_info.update_access()
            if session_info.state == SessionState.IDLE:
                session_info.state = SessionState.ACTIVE
        return session_info
    
    def assign_worker(self, session_id: str, worker_id: str) -> bool:
        """Assign a session to a specific worker."""
        session_info = self.sessions.get(session_id)
        if not session_info:
            return False
        
        # Remove from old worker tracking
        if session_info.worker_id:
            old_worker_sessions = self.worker_sessions.get(session_info.worker_id)
            if old_worker_sessions:
                old_worker_sessions.discard(session_id)
        
        # Assign to new worker
        session_info.worker_id = worker_id
        if worker_id not in self.worker_sessions:
            self.worker_sessions[worker_id] = set()
        self.worker_sessions[worker_id].add(session_id)
        
        logger.info(f"Assigned session {session_id} to worker {worker_id}")
        return True
    
    async def migrate_session(self, session_id: str, from_worker: str, to_worker: str) -> bool:
        """Migrate a session from one worker to another."""
        session_info = self.sessions.get(session_id)
        if not session_info or session_info.worker_id != from_worker:
            return False
        
        logger.info(f"Migrating session {session_id} from {from_worker} to {to_worker}")
        
        try:
            session_info.state = SessionState.MIGRATING
            
            # For stateful sessions, we would need to serialize/deserialize state
            if session_info.requires_state_persistence():
                await self._migrate_session_state(session_info, from_worker, to_worker)
            
            # Update worker assignment
            self.assign_worker(session_id, to_worker)
            session_info.state = SessionState.ACTIVE
            
            logger.info(f"Successfully migrated session {session_id} to {to_worker}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate session {session_id}: {e}")
            session_info.state = SessionState.ACTIVE  # Revert to original worker
            return False
    
    async def _migrate_session_state(self, session_info: SessionInfo, from_worker: str, to_worker: str):
        """Migrate session state between workers (placeholder for future implementation)."""
        # This would be implemented based on specific state types
        # For now, we just log the migration intent
        
        if session_info.session_type == SessionType.IPYTHON:
            logger.info(f"Would migrate IPython kernel {session_info.ipython_kernel_id}")
            # Future: Serialize kernel state, transfer to new worker, restore
        
        if session_info.session_type == SessionType.FILE_CONTEXT:
            logger.info(f"Would migrate file context from {session_info.working_directory}")
            # Future: Transfer working directory state, open file handles
        
        # For now, just reset state-specific info since we can't actually migrate
        session_info.ipython_kernel_id = None
        session_info.working_directory = None
        session_info.open_files.clear()
    
    def terminate_session(self, session_id: str) -> bool:
        """Terminate a session and clean up resources."""
        session_info = self.sessions.get(session_id)
        if not session_info:
            return False
        
        logger.info(f"Terminating session {session_id}")
        
        session_info.state = SessionState.TERMINATED
        
        # Remove from worker tracking
        if session_info.worker_id:
            worker_sessions = self.worker_sessions.get(session_info.worker_id)
            if worker_sessions:
                worker_sessions.discard(session_id)
        
        # Remove from sessions
        del self.sessions[session_id]
        
        return True
    
    def get_worker_sessions(self, worker_id: str) -> Set[str]:
        """Get all sessions assigned to a worker."""
        return self.worker_sessions.get(worker_id, set()).copy()
    
    def cleanup_worker_sessions(self, worker_id: str):
        """Clean up all sessions for a failed worker."""
        session_ids = self.get_worker_sessions(worker_id)
        
        logger.info(f"Cleaning up {len(session_ids)} sessions for failed worker {worker_id}")
        
        for session_id in session_ids:
            session_info = self.sessions.get(session_id)
            if session_info:
                if session_info.requires_state_persistence():
                    # Mark for migration rather than termination
                    session_info.state = SessionState.IDLE
                    session_info.worker_id = None
                    logger.info(f"Session {session_id} marked for migration")
                else:
                    # Ephemeral sessions can be terminated
                    self.terminate_session(session_id)
        
        # Clear worker session tracking
        self.worker_sessions.pop(worker_id, None)
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session_info in self.sessions.items():
            timeout = session_info.metadata.get('timeout', self.default_timeout)
            if session_info.is_expired(timeout):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            logger.info(f"Cleaning up expired session {session_id}")
            self.terminate_session(session_id)
    
    def _force_cleanup_oldest_sessions(self, count: int = 10):
        """Force cleanup of oldest idle sessions to make room."""
        # Sort by last access time (oldest first)
        idle_sessions = [
            (session_id, session_info) for session_id, session_info in self.sessions.items()
            if session_info.state == SessionState.IDLE
        ]
        idle_sessions.sort(key=lambda x: x[1].last_accessed)
        
        # Remove oldest sessions
        for i, (session_id, _) in enumerate(idle_sessions[:count]):
            logger.info(f"Force cleaning up old session {session_id}")
            self.terminate_session(session_id)
    
    async def _cleanup_loop(self):
        """Background cleanup task."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session manager statistics."""
        active_sessions = sum(1 for s in self.sessions.values() if s.state == SessionState.ACTIVE)
        idle_sessions = sum(1 for s in self.sessions.values() if s.state == SessionState.IDLE)
        migrating_sessions = sum(1 for s in self.sessions.values() if s.state == SessionState.MIGRATING)
        
        stateful_sessions = sum(1 for s in self.sessions.values() if s.requires_state_persistence())
        
        return {
            'total_sessions': len(self.sessions),
            'active_sessions': active_sessions,
            'idle_sessions': idle_sessions,
            'migrating_sessions': migrating_sessions,
            'stateful_sessions': stateful_sessions,
            'workers_with_sessions': len([w for w in self.worker_sessions.values() if w]),
            'average_session_age': sum(
                time.time() - s.created_at for s in self.sessions.values()
            ) / max(1, len(self.sessions))
        }
    
    async def shutdown(self):
        """Shutdown the session manager."""
        logger.info("Shutting down session manager")
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Terminate all sessions
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            self.terminate_session(session_id)
        
        self._initialized = False
        logger.info("Session manager shutdown complete")