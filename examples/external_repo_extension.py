"""Example of how an external repository can extend OpenHands.

This demonstrates the proper way for external repositories to build upon OpenHands
without relying on environment variables or global state. The external repo can:

1. Create its own FastAPI app with custom context
2. Add its own routes and middleware
3. Include OpenHands routes as needed
4. Override specific behaviors through dependency injection

This approach eliminates the need for environment variable configuration
and allows clean separation between OpenHands core and extensions.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from openhands.server.context.server_context import ServerContext
from openhands.server.factory import create_openhands_app


# Step 1: Create your custom ServerContext
class ExternalRepoContext(ServerContext):
    """Custom context for external repository with enterprise features."""
    
    def __init__(self, tenant_id: str = 'default', user_id: Optional[str] = None):
        super().__init__()
        self.tenant_id = tenant_id
        self.user_id = user_id
        self._custom_config = None
    
    def get_config(self):
        """Override config with tenant-specific settings."""
        config = super().get_config()
        
        # Add tenant-specific configuration
        config.update({
            'tenant_id': self.tenant_id,
            'custom_storage_path': f'/data/tenants/{self.tenant_id}',
            'custom_feature_flags': {
                'enterprise_features': True,
                'advanced_analytics': True,
            }
        })
        
        return config
    
    def get_server_config(self):
        """Override server config for enterprise deployment."""
        server_config = super().get_server_config()
        
        # Customize for enterprise
        server_config.app_mode = 'ENTERPRISE'  # Custom app mode
        server_config.enable_billing = True
        server_config.hide_llm_settings = False
        
        return server_config
    
    def get_file_store(self):
        """Use tenant-isolated file storage."""
        # In a real implementation, this would return a tenant-aware file store
        file_store = super().get_file_store()
        # Customize file store for tenant isolation
        return file_store


# Step 2: Create your custom lifespan (optional)
@asynccontextmanager
async def external_repo_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Custom lifespan for external repo initialization."""
    print("🚀 Starting external repo services...")
    
    # Initialize your custom services here
    # e.g., database connections, external API clients, etc.
    
    yield
    
    print("🛑 Shutting down external repo services...")
    # Cleanup your custom services here


# Step 3: Create context factory for your needs
def create_external_context(tenant_id: str = 'default') -> ExternalRepoContext:
    """Factory function to create context instances."""
    return ExternalRepoContext(tenant_id=tenant_id)


# Step 4: Create your FastAPI app with OpenHands integration
def create_external_app() -> FastAPI:
    """Create the external repository's FastAPI application."""
    
    # Option A: Create OpenHands app with your custom context
    openhands_app = create_openhands_app(
        context_factory=lambda: create_external_context(),
        include_oss_routes=False,  # Skip OSS routes for enterprise
        custom_lifespan=external_repo_lifespan,
        title='My Enterprise Platform',
        description='Enterprise platform built on OpenHands'
    )
    
    # Option B: Create your own app and mount OpenHands
    main_app = FastAPI(
        title='My Enterprise Platform',
        description='Enterprise platform with OpenHands integration',
        version='1.0.0'
    )
    
    # Add your custom routes
    @main_app.get('/enterprise/status')
    async def enterprise_status():
        return {'status': 'running', 'mode': 'enterprise'}
    
    @main_app.get('/enterprise/tenant/{tenant_id}/info')
    async def tenant_info(
        tenant_id: str,
        request: Request,
        # Use dependency injection to get context
        context: ServerContext = Depends(lambda r: create_external_context(tenant_id))
    ):
        config = context.get_config()
        return {
            'tenant_id': tenant_id,
            'storage_path': config.get('custom_storage_path'),
            'features': config.get('custom_feature_flags', {})
        }
    
    # Add custom middleware
    @main_app.middleware('http')
    async def tenant_middleware(request: Request, call_next):
        # Extract tenant from header or path
        tenant_id = request.headers.get('X-Tenant-ID', 'default')
        request.state.tenant_id = tenant_id
        
        response = await call_next(request)
        response.headers['X-Tenant-ID'] = tenant_id
        return response
    
    # Mount OpenHands app at a subpath
    main_app.mount('/openhands', openhands_app)
    
    return main_app


# Step 5: Alternative approach - extend OpenHands app directly
def create_extended_openhands_app() -> FastAPI:
    """Alternative: extend OpenHands app directly with custom routes."""
    
    app = create_openhands_app(
        context_factory=lambda: create_external_context(),
        custom_lifespan=external_repo_lifespan
    )
    
    # Add your routes to the OpenHands app
    @app.get('/api/enterprise/dashboard')
    async def enterprise_dashboard(
        request: Request,
        context: ServerContext = Depends(lambda r: create_external_context())
    ):
        config = context.get_config()
        return {
            'dashboard_data': 'enterprise_metrics',
            'tenant_features': config.get('custom_feature_flags', {})
        }
    
    return app


# Example usage in external repo's main.py
if __name__ == '__main__':
    import uvicorn
    
    # Choose your approach
    app = create_external_app()  # Full custom app with OpenHands mounted
    # app = create_extended_openhands_app()  # Extended OpenHands app
    
    # Run the server
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8000,
        reload=True
    )


# Example of how to test the integration
def test_external_integration():
    """Test that the external integration works correctly."""
    from fastapi.testclient import TestClient
    
    app = create_external_app()
    client = TestClient(app)
    
    # Test custom routes
    response = client.get('/enterprise/status')
    assert response.status_code == 200
    assert response.json()['mode'] == 'enterprise'
    
    # Test tenant-specific routes
    response = client.get('/enterprise/tenant/acme-corp/info')
    assert response.status_code == 200
    data = response.json()
    assert data['tenant_id'] == 'acme-corp'
    assert 'enterprise_features' in data['features']
    
    # Test OpenHands routes still work
    response = client.get('/openhands/api/health')
    assert response.status_code == 200
    
    print("✅ All integration tests passed!")


if __name__ == '__main__':
    # Run tests
    test_external_integration()