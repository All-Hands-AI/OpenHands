# OpenHands API Design Guide

This guide covers API design patterns, service interfaces, and API management for OpenHands systems.

## Table of Contents
1. [REST API Design](#rest-api-design)
2. [GraphQL Integration](#graphql-integration)
3. [WebSocket Services](#websocket-services)
4. [API Gateway](#api-gateway)

## REST API Design

### 1. API Router

Implementation of REST API routing system:

```python
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import asyncio
import json

class APIResponse(BaseModel):
    """Standard API response"""
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[dict] = None

class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"

class APIRouterManager:
    """Manage API routes and versioning"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.routers: Dict[str, APIRouter] = {}
        self.middlewares: List[Callable] = []
        
    def create_router(
        self,
        version: str,
        prefix: str,
        tags: List[str]
    ) -> APIRouter:
        """Create versioned API router"""
        router = APIRouter(prefix=f"/api/{version}/{prefix}")
        
        # Add standard response wrapper
        @router.middleware("http")
        async def response_middleware(request, call_next):
            try:
                response = await call_next(request)
                return APIResponse(
                    success=True,
                    data=response
                )
            except HTTPException as e:
                return APIResponse(
                    success=False,
                    error=str(e),
                    metadata={'status_code': e.status_code}
                )
            except Exception as e:
                return APIResponse(
                    success=False,
                    error="Internal server error",
                    metadata={'detail': str(e)}
                )
                
        # Add custom middlewares
        for middleware in self.middlewares:
            router.middleware("http")(middleware)
            
        self.routers[f"{version}/{prefix}"] = router
        self.app.include_router(router, tags=tags)
        
        return router
        
    def add_middleware(self, middleware: Callable):
        """Add middleware to all routers"""
        self.middlewares.append(middleware)
        
class APIEndpoint:
    """Base API endpoint implementation"""
    
    def __init__(
        self,
        router: APIRouter,
        path: str,
        methods: List[str]
    ):
        self.router = router
        self.path = path
        self.methods = methods
        
    def register(self):
        """Register endpoint with router"""
        for method in self.methods:
            handler = getattr(self, f"handle_{method.lower()}")
            self.router.add_api_route(
                self.path,
                handler,
                methods=[method]
            )
            
    async def handle_get(self):
        """Handle GET request"""
        raise NotImplementedError
        
    async def handle_post(self):
        """Handle POST request"""
        raise NotImplementedError
        
    async def handle_put(self):
        """Handle PUT request"""
        raise NotImplementedError
        
    async def handle_delete(self):
        """Handle DELETE request"""
        raise NotImplementedError
```

### 2. API Documentation

Implementation of API documentation:

```python
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import yaml

@dataclass
class APIEndpointDoc:
    """API endpoint documentation"""
    path: str
    method: str
    summary: str
    description: str
    parameters: List[dict]
    request_body: Optional[dict]
    responses: Dict[str, dict]
    examples: List[dict]

class APIDocumentation:
    """API documentation generator"""
    
    def __init__(self):
        self.endpoints: Dict[str, APIEndpointDoc] = {}
        
    def add_endpoint(
        self,
        endpoint: APIEndpointDoc
    ):
        """Add endpoint documentation"""
        key = f"{endpoint.method.upper()} {endpoint.path}"
        self.endpoints[key] = endpoint
        
    def generate_openapi(self) -> dict:
        """Generate OpenAPI specification"""
        spec = {
            'openapi': '3.0.0',
            'info': {
                'title': 'OpenHands API',
                'version': '1.0.0',
                'description': 'OpenHands REST API'
            },
            'paths': {}
        }
        
        # Add endpoints
        for endpoint in self.endpoints.values():
            if endpoint.path not in spec['paths']:
                spec['paths'][endpoint.path] = {}
                
            spec['paths'][endpoint.path][endpoint.method.lower()] = {
                'summary': endpoint.summary,
                'description': endpoint.description,
                'parameters': endpoint.parameters,
                'requestBody': endpoint.request_body,
                'responses': endpoint.responses
            }
            
        return spec
        
    def generate_markdown(self) -> str:
        """Generate markdown documentation"""
        docs = ["# API Documentation\n"]
        
        for endpoint in self.endpoints.values():
            docs.extend([
                f"## {endpoint.method} {endpoint.path}\n",
                f"{endpoint.description}\n",
                "### Parameters\n"
            ])
            
            # Add parameters
            for param in endpoint.parameters:
                docs.append(
                    f"- `{param['name']}` ({param['type']}): "
                    f"{param['description']}\n"
                )
                
            # Add request body
            if endpoint.request_body:
                docs.extend([
                    "\n### Request Body\n",
                    "```json\n",
                    json.dumps(
                        endpoint.request_body,
                        indent=2
                    ),
                    "\n```\n"
                ])
                
            # Add responses
            docs.append("\n### Responses\n")
            for status, response in endpoint.responses.items():
                docs.extend([
                    f"#### {status}\n",
                    f"{response['description']}\n",
                    "```json\n",
                    json.dumps(
                        response['content'],
                        indent=2
                    ),
                    "\n```\n"
                ])
                
        return '\n'.join(docs)
```

## GraphQL Integration

### 1. GraphQL Schema

Implementation of GraphQL schema:

```python
import strawberry
from typing import List, Optional
from dataclasses import dataclass

@strawberry.type
class Query:
    """GraphQL query definitions"""
    
    @strawberry.field
    async def get_agent(
        self,
        agent_id: str
    ) -> 'Agent':
        """Get agent by ID"""
        # Implement agent retrieval
        pass
        
    @strawberry.field
    async def list_agents(
        self,
        status: Optional[str] = None
    ) -> List['Agent']:
        """List all agents"""
        # Implement agent listing
        pass
        
    @strawberry.field
    async def get_task(
        self,
        task_id: str
    ) -> 'Task':
        """Get task by ID"""
        # Implement task retrieval
        pass

@strawberry.type
class Mutation:
    """GraphQL mutation definitions"""
    
    @strawberry.mutation
    async def create_agent(
        self,
        input: 'CreateAgentInput'
    ) -> 'Agent':
        """Create new agent"""
        # Implement agent creation
        pass
        
    @strawberry.mutation
    async def update_agent(
        self,
        agent_id: str,
        input: 'UpdateAgentInput'
    ) -> 'Agent':
        """Update agent"""
        # Implement agent update
        pass
        
    @strawberry.mutation
    async def delete_agent(
        self,
        agent_id: str
    ) -> bool:
        """Delete agent"""
        # Implement agent deletion
        pass

@strawberry.type
class Subscription:
    """GraphQL subscription definitions"""
    
    @strawberry.subscription
    async def agent_events(
        self,
        agent_id: str
    ) -> 'AgentEvent':
        """Subscribe to agent events"""
        # Implement event subscription
        pass
```

## WebSocket Services

### 1. WebSocket Manager

Implementation of WebSocket services:

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, Any
import asyncio
import json

class WebSocketManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.handlers: Dict[str, Callable] = {}
        
    async def connect(
        self,
        websocket: WebSocket,
        client_id: str
    ):
        """Handle new connection"""
        await websocket.accept()
        
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        self.active_connections[client_id].add(websocket)
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_json()
                
                # Handle message
                await self._handle_message(
                    websocket,
                    client_id,
                    data
                )
                
        except WebSocketDisconnect:
            self.disconnect(websocket, client_id)
            
    def disconnect(
        self,
        websocket: WebSocket,
        client_id: str
    ):
        """Handle disconnection"""
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(
                websocket
            )
            
    async def broadcast(
        self,
        message: Any,
        client_id: Optional[str] = None
    ):
        """Broadcast message to clients"""
        if client_id:
            # Send to specific client
            connections = self.active_connections.get(
                client_id,
                set()
            )
        else:
            # Send to all clients
            connections = set().union(
                *self.active_connections.values()
            )
            
        # Send message
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(
                    f"Failed to send message: {e}"
                )
                
    def register_handler(
        self,
        message_type: str,
        handler: Callable
    ):
        """Register message handler"""
        self.handlers[message_type] = handler
        
    async def _handle_message(
        self,
        websocket: WebSocket,
        client_id: str,
        message: dict
    ):
        """Handle received message"""
        message_type = message.get('type')
        if not message_type:
            await websocket.send_json({
                'error': 'Missing message type'
            })
            return
            
        handler = self.handlers.get(message_type)
        if not handler:
            await websocket.send_json({
                'error': f'Unknown message type: {message_type}'
            })
            return
            
        try:
            response = await handler(
                client_id,
                message.get('data')
            )
            await websocket.send_json(response)
        except Exception as e:
            await websocket.send_json({
                'error': str(e)
            })
```

## API Gateway

### 1. Gateway Implementation

Implementation of API gateway:

```python
class APIGateway:
    """API gateway implementation"""
    
    def __init__(self):
        self.routes: Dict[str, dict] = {}
        self.middlewares: List[Callable] = []
        self.rate_limiters: Dict[str, RateLimiter] = {}
        
    def add_route(
        self,
        path: str,
        target: str,
        methods: List[str],
        auth_required: bool = True,
        rate_limit: Optional[dict] = None
    ):
        """Add API route"""
        self.routes[path] = {
            'target': target,
            'methods': methods,
            'auth_required': auth_required
        }
        
        # Setup rate limiting
        if rate_limit:
            self.rate_limiters[path] = RateLimiter(
                **rate_limit
            )
            
    async def handle_request(
        self,
        path: str,
        method: str,
        headers: dict,
        body: Any
    ) -> Any:
        """Handle API request"""
        # Check route
        route = self.routes.get(path)
        if not route:
            raise HTTPException(
                status_code=404,
                detail="Route not found"
            )
            
        # Check method
        if method not in route['methods']:
            raise HTTPException(
                status_code=405,
                detail="Method not allowed"
            )
            
        # Apply middlewares
        request = await self._apply_middlewares(
            path,
            method,
            headers,
            body
        )
            
        # Check authentication
        if route['auth_required']:
            await self._authenticate(request)
            
        # Check rate limit
        if path in self.rate_limiters:
            await self.rate_limiters[path].check_rate(
                request
            )
            
        # Forward request
        return await self._forward_request(
            route['target'],
            request
        )
        
    async def _apply_middlewares(
        self,
        path: str,
        method: str,
        headers: dict,
        body: Any
    ) -> dict:
        """Apply middleware chain"""
        request = {
            'path': path,
            'method': method,
            'headers': headers,
            'body': body
        }
        
        for middleware in self.middlewares:
            request = await middleware(request)
            
        return request
        
    async def _authenticate(self, request: dict):
        """Authenticate request"""
        auth_header = request['headers'].get(
            'Authorization'
        )
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Missing authentication"
            )
            
        # Implement authentication logic
        pass
        
    async def _forward_request(
        self,
        target: str,
        request: dict
    ) -> Any:
        """Forward request to target"""
        async with aiohttp.ClientSession() as session:
            async with session.request(
                request['method'],
                f"{target}{request['path']}",
                headers=request['headers'],
                json=request['body']
            ) as response:
                return await response.json()

class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(
        self,
        requests: int,
        window: int
    ):
        self.requests = requests
        self.window = window
        self.counters: Dict[str, List[float]] = {}
        
    async def check_rate(self, request: dict):
        """Check rate limit"""
        key = self._get_key(request)
        now = time.time()
        
        # Initialize counter
        if key not in self.counters:
            self.counters[key] = []
            
        # Clean old timestamps
        self.counters[key] = [
            ts for ts in self.counters[key]
            if now - ts <= self.window
        ]
        
        # Check limit
        if len(self.counters[key]) >= self.requests:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )
            
        # Add timestamp
        self.counters[key].append(now)
        
    def _get_key(self, request: dict) -> str:
        """Get rate limit key"""
        # Use IP address or user ID
        return request['headers'].get(
            'X-Forwarded-For',
            'unknown'
        )
```

Remember to:
- Document API endpoints
- Implement proper validation
- Handle authentication
- Manage rate limiting
- Monitor API usage
- Version APIs appropriately
- Handle errors consistently