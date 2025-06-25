"""VSCode Integration API Routes

Provides endpoints for VSCode extension registration, discovery, and management.
Implements the server-side registry for the Lazy Connection Pattern.
"""

import time
import uuid
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi import status as http_status
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.server.dependencies import get_dependencies

app = APIRouter(prefix='/api/vscode', dependencies=get_dependencies())

# Global VSCode instance registry
# In production, this could be moved to a persistent store
_vscode_registry: Dict[str, 'VSCodeInstance'] = {}


class VSCodeInstance(BaseModel):
    """Information about a registered VSCode instance"""
    connection_id: str
    workspace_path: str
    workspace_name: str
    vscode_version: str
    extension_version: str
    capabilities: List[str]
    registered_at: float
    last_heartbeat: float
    status: str = "active"  # active, idle, disconnected


class VSCodeRegistrationRequest(BaseModel):
    """Request payload for VSCode instance registration"""
    workspace_path: str
    workspace_name: str
    vscode_version: str
    extension_version: str
    capabilities: List[str] = []


class VSCodeRegistrationResponse(BaseModel):
    """Response for successful VSCode registration"""
    connection_id: str
    message: str


class VSCodeInstanceInfo(BaseModel):
    """Public information about a VSCode instance"""
    connection_id: str
    workspace_name: str
    workspace_path: str
    status: str
    registered_at: float
    last_heartbeat: float


@app.post('/register', response_model=VSCodeRegistrationResponse)
async def register_vscode_instance(request: VSCodeRegistrationRequest):
    """Register a new VSCode instance with the server
    
    This endpoint is called by the VSCode extension when it connects to OpenHands.
    It creates a unique connection_id and stores the instance information.
    """
    try:
        # Generate unique connection ID
        connection_id = str(uuid.uuid4())
        current_time = time.time()
        
        # Create VSCode instance record
        instance = VSCodeInstance(
            connection_id=connection_id,
            workspace_path=request.workspace_path,
            workspace_name=request.workspace_name,
            vscode_version=request.vscode_version,
            extension_version=request.extension_version,
            capabilities=request.capabilities,
            registered_at=current_time,
            last_heartbeat=current_time,
            status="active"
        )
        
        # Store in registry
        _vscode_registry[connection_id] = instance
        
        logger.info(f"Registered VSCode instance: {connection_id} for workspace '{request.workspace_name}'")
        
        return VSCodeRegistrationResponse(
            connection_id=connection_id,
            message=f"Successfully registered VSCode instance for workspace '{request.workspace_name}'"
        )
        
    except Exception as e:
        logger.error(f"Failed to register VSCode instance: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@app.get('/instances', response_model=List[VSCodeInstanceInfo])
async def get_vscode_instances():
    """Get list of all registered VSCode instances
    
    This endpoint is used by VsCodeRuntime to discover available VSCode instances.
    Returns public information about each registered instance.
    """
    try:
        # Clean up stale instances (no heartbeat for > 5 minutes)
        current_time = time.time()
        stale_threshold = 5 * 60  # 5 minutes
        
        stale_ids = [
            conn_id for conn_id, instance in _vscode_registry.items()
            if current_time - instance.last_heartbeat > stale_threshold
        ]
        
        for conn_id in stale_ids:
            logger.info(f"Removing stale VSCode instance: {conn_id}")
            del _vscode_registry[conn_id]
        
        # Return active instances
        instances = [
            VSCodeInstanceInfo(
                connection_id=instance.connection_id,
                workspace_name=instance.workspace_name,
                workspace_path=instance.workspace_path,
                status=instance.status,
                registered_at=instance.registered_at,
                last_heartbeat=instance.last_heartbeat
            )
            for instance in _vscode_registry.values()
        ]
        
        logger.debug(f"Returning {len(instances)} VSCode instances")
        return instances
        
    except Exception as e:
        logger.error(f"Failed to get VSCode instances: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve instances: {str(e)}"
        )


@app.post('/heartbeat/{connection_id}')
async def vscode_heartbeat(connection_id: str):
    """Update heartbeat for a VSCode instance
    
    This endpoint should be called periodically by VSCode extensions
    to indicate they are still active and connected.
    """
    try:
        if connection_id not in _vscode_registry:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"VSCode instance {connection_id} not found"
            )
        
        # Update heartbeat timestamp
        _vscode_registry[connection_id].last_heartbeat = time.time()
        _vscode_registry[connection_id].status = "active"
        
        logger.debug(f"Updated heartbeat for VSCode instance: {connection_id}")
        return {"message": "Heartbeat updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update heartbeat for {connection_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Heartbeat update failed: {str(e)}"
        )


@app.delete('/unregister/{connection_id}')
async def unregister_vscode_instance(connection_id: str):
    """Unregister a VSCode instance
    
    This endpoint is called when a VSCode instance disconnects
    or is no longer available.
    """
    try:
        if connection_id not in _vscode_registry:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"VSCode instance {connection_id} not found"
            )
        
        instance = _vscode_registry[connection_id]
        del _vscode_registry[connection_id]
        
        logger.info(f"Unregistered VSCode instance: {connection_id} for workspace '{instance.workspace_name}'")
        return {"message": f"Successfully unregistered VSCode instance {connection_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unregister VSCode instance {connection_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unregistration failed: {str(e)}"
        )


@app.get('/instance/{connection_id}', response_model=VSCodeInstanceInfo)
async def get_vscode_instance(connection_id: str):
    """Get information about a specific VSCode instance"""
    try:
        if connection_id not in _vscode_registry:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"VSCode instance {connection_id} not found"
            )
        
        instance = _vscode_registry[connection_id]
        return VSCodeInstanceInfo(
            connection_id=instance.connection_id,
            workspace_name=instance.workspace_name,
            workspace_path=instance.workspace_path,
            status=instance.status,
            registered_at=instance.registered_at,
            last_heartbeat=instance.last_heartbeat
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get VSCode instance {connection_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve instance: {str(e)}"
        )


@app.get('/registry/stats')
async def get_registry_stats():
    """Get statistics about the VSCode registry
    
    Useful for monitoring and debugging.
    """
    try:
        current_time = time.time()
        total_instances = len(_vscode_registry)
        
        # Count by status
        status_counts: Dict[str, int] = {}
        for instance in _vscode_registry.values():
            status = instance.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count recent activity (last 5 minutes)
        recent_threshold = 5 * 60  # 5 minutes
        recent_activity = sum(
            1 for instance in _vscode_registry.values()
            if current_time - instance.last_heartbeat < recent_threshold
        )
        
        return {
            "total_instances": total_instances,
            "status_counts": status_counts,
            "recent_activity": recent_activity,
            "registry_size": len(_vscode_registry)
        }
        
    except Exception as e:
        logger.error(f"Failed to get registry stats: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stats: {str(e)}"
        )