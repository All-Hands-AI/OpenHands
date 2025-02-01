# OpenHands Integrations and Extensibility Guide

This guide covers how to extend OpenHands with external integrations and custom functionality.

## Table of Contents
1. [Custom Runtime Extensions](#custom-runtime-extensions)
2. [External Service Integrations](#external-service-integrations)
3. [Plugin System](#plugin-system)
4. [Custom Agent Capabilities](#custom-agent-capabilities)

## Custom Runtime Extensions

### 1. Custom Runtime Implementation

Example of extending the runtime system with custom capabilities:

```python
from openhands.runtime.base import Runtime
from openhands.events.action import Action
from openhands.events.observation import Observation
from typing import Dict, Any

class ExtendedRuntime(Runtime):
    """Extended runtime with custom capabilities"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.custom_capabilities = {
            'database_query': self._handle_database_query,
            'api_request': self._handle_api_request,
            'file_transform': self._handle_file_transform
        }
        
    async def execute(self, action: Action) -> Observation:
        """Execute action with custom capabilities"""
        # Check for custom action types
        if action.type in self.custom_capabilities:
            return await self.custom_capabilities[action.type](action)
            
        # Fall back to standard execution
        return await super().execute(action)
        
    async def _handle_database_query(self, action: Action) -> Observation:
        """Handle database query actions"""
        try:
            # Execute database query
            async with self.db_pool.acquire() as conn:
                result = await conn.fetch(action.query, *action.params)
                return Observation(
                    content=result,
                    metadata={'rows': len(result)}
                )
        except Exception as e:
            return ErrorObservation(str(e))
            
    async def _handle_api_request(self, action: Action) -> Observation:
        """Handle external API requests"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    action.method,
                    action.url,
                    json=action.data
                ) as response:
                    data = await response.json()
                    return Observation(
                        content=data,
                        metadata={'status': response.status}
                    )
        except Exception as e:
            return ErrorObservation(str(e))
```

### 2. Custom Action Types

Example of implementing custom action types:

```python
from dataclasses import dataclass
from openhands.events.action import Action
from typing import Optional, Dict, Any

@dataclass
class DatabaseQueryAction(Action):
    """Action for database operations"""
    query: str
    params: tuple = ()
    type: str = "database_query"
    
    def validate(self) -> bool:
        """Validate query action"""
        return bool(self.query.strip())

@dataclass
class APIRequestAction(Action):
    """Action for API requests"""
    method: str
    url: str
    data: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    type: str = "api_request"
    
    def validate(self) -> bool:
        """Validate API request action"""
        return bool(self.url.strip()) and self.method in [
            'GET', 'POST', 'PUT', 'DELETE'
        ]

class CustomActionRegistry:
    """Registry for custom action types"""
    
    def __init__(self):
        self.actions = {}
        
    def register_action(self, action_class: type):
        """Register custom action type"""
        action_type = action_class.type
        if action_type in self.actions:
            raise ValueError(f"Action type {action_type} already registered")
            
        self.actions[action_type] = action_class
        
    def get_action_class(self, action_type: str) -> type:
        """Get action class by type"""
        if action_type not in self.actions:
            raise ValueError(f"Unknown action type: {action_type}")
            
        return self.actions[action_type]
```

## External Service Integrations

### 1. Service Integration Framework

Framework for integrating external services:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ServiceIntegration(ABC):
    """Base class for service integrations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        
    @abstractmethod
    async def initialize(self):
        """Initialize service connection"""
        pass
        
    @abstractmethod
    async def cleanup(self):
        """Cleanup service resources"""
        pass
        
    @abstractmethod
    async def health_check(self) -> bool:
        """Check service health"""
        pass

class ServiceRegistry:
    """Registry for service integrations"""
    
    def __init__(self):
        self.services: Dict[str, ServiceIntegration] = {}
        
    async def register_service(
        self,
        name: str,
        service: ServiceIntegration
    ):
        """Register and initialize service"""
        if name in self.services:
            raise ValueError(f"Service {name} already registered")
            
        await service.initialize()
        self.services[name] = service
        
    async def get_service(
        self,
        name: str
    ) -> Optional[ServiceIntegration]:
        """Get registered service"""
        return self.services.get(name)
        
    async def cleanup(self):
        """Cleanup all services"""
        for service in self.services.values():
            await service.cleanup()
```

### 2. Example Service Implementations

Examples of specific service integrations:

```python
class ElasticsearchIntegration(ServiceIntegration):
    """Elasticsearch integration"""
    
    async def initialize(self):
        """Initialize Elasticsearch client"""
        self.client = AsyncElasticsearch(
            hosts=self.config['hosts'],
            basic_auth=(
                self.config['username'],
                self.config['password']
            )
        )
        
    async def cleanup(self):
        """Cleanup Elasticsearch client"""
        if self.client:
            await self.client.close()
            
    async def health_check(self) -> bool:
        """Check Elasticsearch health"""
        try:
            health = await self.client.cluster.health()
            return health['status'] in ['green', 'yellow']
        except Exception:
            return False
            
    async def search(self, index: str, query: dict) -> dict:
        """Perform Elasticsearch search"""
        return await self.client.search(
            index=index,
            body=query
        )

class RedisIntegration(ServiceIntegration):
    """Redis integration"""
    
    async def initialize(self):
        """Initialize Redis client"""
        self.client = aioredis.from_url(
            self.config['url'],
            password=self.config.get('password')
        )
        
    async def cleanup(self):
        """Cleanup Redis client"""
        if self.client:
            await self.client.close()
            
    async def health_check(self) -> bool:
        """Check Redis health"""
        try:
            return await self.client.ping()
        except Exception:
            return False
            
    async def cache_get(self, key: str) -> Any:
        """Get cached value"""
        value = await self.client.get(key)
        return json.loads(value) if value else None
        
    async def cache_set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """Set cached value"""
        await self.client.set(
            key,
            json.dumps(value),
            ex=ttl
        )
```

## Plugin System

### 1. Plugin Framework

Framework for creating and managing plugins:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class Plugin(ABC):
    """Base class for plugins"""
    
    @abstractmethod
    async def initialize(self, context: Dict[str, Any]):
        """Initialize plugin"""
        pass
        
    @abstractmethod
    async def cleanup(self):
        """Cleanup plugin resources"""
        pass
        
    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """List plugin capabilities"""
        pass

class PluginManager:
    """Manager for plugins"""
    
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.capabilities: Dict[str, str] = {}
        
    async def load_plugin(
        self,
        name: str,
        plugin: Plugin,
        context: Dict[str, Any]
    ):
        """Load and initialize plugin"""
        if name in self.plugins:
            raise ValueError(f"Plugin {name} already loaded")
            
        # Initialize plugin
        await plugin.initialize(context)
        self.plugins[name] = plugin
        
        # Register capabilities
        for capability in plugin.capabilities:
            if capability in self.capabilities:
                logger.warning(
                    f"Capability {capability} already registered "
                    f"by {self.capabilities[capability]}"
                )
            self.capabilities[capability] = name
            
    async def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get loaded plugin"""
        return self.plugins.get(name)
        
    async def get_plugin_for_capability(
        self,
        capability: str
    ) -> Optional[Plugin]:
        """Get plugin that provides capability"""
        plugin_name = self.capabilities.get(capability)
        if plugin_name:
            return self.plugins.get(plugin_name)
        return None
```

### 2. Example Plugin Implementations

Examples of specific plugins:

```python
class DataTransformationPlugin(Plugin):
    """Plugin for data transformations"""
    
    async def initialize(self, context: Dict[str, Any]):
        """Initialize transformation engines"""
        self.transformers = {
            'json_to_csv': self._json_to_csv,
            'csv_to_json': self._csv_to_json,
            'xml_to_json': self._xml_to_json
        }
        
    async def cleanup(self):
        """Cleanup resources"""
        pass
        
    @property
    def capabilities(self) -> List[str]:
        return [
            'transform_data',
            'format_conversion',
            'data_validation'
        ]
        
    async def transform(
        self,
        data: Any,
        source_format: str,
        target_format: str
    ) -> Any:
        """Transform data between formats"""
        transform_key = f"{source_format}_to_{target_format}"
        if transform_key not in self.transformers:
            raise ValueError(f"Unsupported transformation: {transform_key}")
            
        return await self.transformers[transform_key](data)

class AuthenticationPlugin(Plugin):
    """Plugin for authentication services"""
    
    async def initialize(self, context: Dict[str, Any]):
        """Initialize authentication providers"""
        self.providers = {
            'oauth': self._handle_oauth,
            'jwt': self._handle_jwt,
            'basic': self._handle_basic
        }
        self.tokens = {}
        
    async def cleanup(self):
        """Cleanup authentication resources"""
        self.tokens.clear()
        
    @property
    def capabilities(self) -> List[str]:
        return [
            'authenticate',
            'authorize',
            'token_validation'
        ]
        
    async def authenticate(
        self,
        provider: str,
        credentials: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Authenticate using specified provider"""
        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}")
            
        return await self.providers[provider](credentials)
```

## Custom Agent Capabilities

### 1. Agent Extension Framework

Framework for extending agent capabilities:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class AgentCapability(ABC):
    """Base class for agent capabilities"""
    
    @abstractmethod
    async def initialize(self, context: Dict[str, Any]):
        """Initialize capability"""
        pass
        
    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Process input with capability"""
        pass
        
    @property
    @abstractmethod
    def requirements(self) -> List[str]:
        """List capability requirements"""
        pass

class ExtensibleAgent(Agent):
    """Agent that supports custom capabilities"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.capabilities: Dict[str, AgentCapability] = {}
        
    async def add_capability(
        self,
        name: str,
        capability: AgentCapability,
        context: Dict[str, Any]
    ):
        """Add new capability to agent"""
        if name in self.capabilities:
            raise ValueError(f"Capability {name} already exists")
            
        # Check requirements
        for requirement in capability.requirements:
            if not await self._check_requirement(requirement):
                raise ValueError(
                    f"Requirement not met: {requirement}"
                )
                
        # Initialize capability
        await capability.initialize(context)
        self.capabilities[name] = capability
        
    async def use_capability(
        self,
        name: str,
        input_data: Any
    ) -> Any:
        """Use specific capability"""
        if name not in self.capabilities:
            raise ValueError(f"Unknown capability: {name}")
            
        return await self.capabilities[name].process(input_data)
```

### 2. Example Capability Implementations

Examples of specific agent capabilities:

```python
class NLPCapability(AgentCapability):
    """Natural Language Processing capability"""
    
    async def initialize(self, context: Dict[str, Any]):
        """Initialize NLP models"""
        self.models = {
            'sentiment': self._load_sentiment_model(),
            'entity': self._load_entity_model(),
            'summary': self._load_summary_model()
        }
        
    async def process(self, input_data: Any) -> Any:
        """Process text with NLP models"""
        if isinstance(input_data, dict):
            text = input_data.get('text', '')
            model = input_data.get('model', 'sentiment')
        else:
            text = str(input_data)
            model = 'sentiment'
            
        if model not in self.models:
            raise ValueError(f"Unknown model: {model}")
            
        return await self.models[model](text)
        
    @property
    def requirements(self) -> List[str]:
        return ['spacy', 'transformers']

class DataAnalysisCapability(AgentCapability):
    """Data analysis capability"""
    
    async def initialize(self, context: Dict[str, Any]):
        """Initialize analysis tools"""
        self.analyzers = {
            'statistics': self._analyze_statistics,
            'clustering': self._analyze_clustering,
            'regression': self._analyze_regression
        }
        
    async def process(self, input_data: Any) -> Any:
        """Analyze data"""
        if not isinstance(input_data, dict):
            raise ValueError("Input must be a dictionary")
            
        analysis_type = input_data.get('type', 'statistics')
        data = input_data.get('data')
        
        if not data:
            raise ValueError("No data provided")
            
        if analysis_type not in self.analyzers:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
            
        return await self.analyzers[analysis_type](data)
        
    @property
    def requirements(self) -> List[str]:
        return ['numpy', 'scipy', 'sklearn']
```

Remember to:
- Document integration interfaces
- Handle errors appropriately
- Implement proper cleanup
- Test integrations thoroughly
- Monitor integration health
- Maintain security standards
- Keep dependencies updated