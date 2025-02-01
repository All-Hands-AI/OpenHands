# OpenHands Initialization Sequence Guide

This guide details the complete initialization sequence of OpenHands, including component dependencies, configuration loading, and startup order. For runtime behavior and component interactions, see [SYSTEM_UNDERSTANDING.md](SYSTEM_UNDERSTANDING.md). For a complete overview, start with [SYSTEM_GUIDE.md](SYSTEM_GUIDE.md).

## System Initialization Flow

### 1. Complete Initialization Sequence
```plaintext
┌─ Pre-Initialization ──────────────────────────────────────────────┐
│ 1. Load Environment Variables                                     │
│ 2. Parse Command Line Arguments                                  │
│ 3. Initialize Logging                                            │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─ Configuration Loading ─────────────────────────────────────────┐
│ 1. Load Default Configuration                                   │
│ 2. Load Config Files                                           │
│ 3. Apply Environment Overrides                                 │
│ 4. Validate Configuration                                      │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─ Core Services Initialization ─────────────────────────────────┐
│ 1. Storage System                                             │
│ 2. Event System                                              │
│ 3. Memory System                                             │
│ 4. LLM Clients                                              │
│ 5. Runtime Environment                                       │
└───────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─ Component Registration ──────────────────────────────────────┐
│ 1. Register Agents                                           │
│ 2. Register Runtime Capabilities                             │
│ 3. Register Event Handlers                                   │
│ 4. Register Memory Providers                                 │
└───────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─ Service Startup ───────────────────────────────────────────┐
│ 1. Start FastAPI Application                               │
│ 2. Initialize Session Manager                              │
│ 3. Setup API Routes                                        │
│ 4. Start Background Tasks                                  │
└─────────────────────────────────────────────────────────────┘
```

### 2. Component Dependencies

```plaintext
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Config     │ ──► │   Storage   │ ──► │   Memory    │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    LLM      │ ──► │   Event     │ ◄── │   Runtime   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Agents    │ ──► │  Session    │ ◄── │   Router    │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Detailed Initialization Steps

### 1. Pre-Initialization Phase
```python
# File: openhands/core/startup.py

async def initialize_system():
    """System initialization sequence"""
    # 1. Load environment
    load_environment()
    
    # 2. Parse arguments
    args = parse_arguments()
    
    # 3. Setup logging
    setup_logging(args.log_level)
    
def load_environment():
    """Load environment variables"""
    # Load .env file if exists
    if os.path.exists('.env'):
        load_dotenv()
        
    # Set required environment variables
    os.environ.setdefault('OPENHANDS_ENV', 'development')
    os.environ.setdefault('OPENHANDS_CONFIG_PATH', 'config')
    
def setup_logging(level: str):
    """Initialize logging system"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
```

### 2. Configuration Loading Phase
```python
# File: openhands/core/config.py

class ConfigurationManager:
    """Manages system configuration"""
    
    def __init__(self):
        self.config = {}
        self.validators = {}
        self.loaded_files = []
        
    async def load_configuration(self):
        """Complete configuration loading sequence"""
        # 1. Load default configuration
        self._load_defaults()
        
        # 2. Load configuration files
        await self._load_config_files()
        
        # 3. Apply environment overrides
        self._apply_environment()
        
        # 4. Validate configuration
        self._validate_configuration()
        
    def _load_defaults(self):
        """Load default configuration"""
        self.config.update({
            'core': {
                'environment': 'development',
                'debug': False,
                'log_level': 'info'
            },
            'server': {
                'host': '0.0.0.0',
                'port': 8000,
                'workers': 1
            },
            'llm': {
                'provider': 'openai',
                'model': 'gpt-4',
                'temperature': 0.7
            }
        })
        
    async def _load_config_files(self):
        """Load configuration from files"""
        config_path = os.environ['OPENHANDS_CONFIG_PATH']
        
        # Load base config
        base_config = f"{config_path}/config.yaml"
        if os.path.exists(base_config):
            self._load_yaml(base_config)
            
        # Load environment specific config
        env = os.environ['OPENHANDS_ENV']
        env_config = f"{config_path}/config.{env}.yaml"
        if os.path.exists(env_config):
            self._load_yaml(env_config)
            
    def _apply_environment(self):
        """Apply environment variable overrides"""
        prefix = 'OPENHANDS_'
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                self._set_config_value(config_key, value)
                
    def _validate_configuration(self):
        """Validate configuration values"""
        for key, validator in self.validators.items():
            value = self._get_config_value(key)
            if not validator(value):
                raise ConfigurationError(f"Invalid value for {key}")
```

### 3. Core Services Initialization
```python
# File: openhands/core/services.py

class ServiceManager:
    """Manages core services"""
    
    def __init__(self, config: Config):
        self.config = config
        self.services = {}
        self.dependencies = self._build_dependencies()
        
    async def initialize_services(self):
        """Initialize all core services"""
        # Initialize in dependency order
        for service_name in self._get_initialization_order():
            await self._initialize_service(service_name)
            
    def _build_dependencies(self) -> Dict[str, Set[str]]:
        """Build service dependency graph"""
        return {
            'storage': set(),  # No dependencies
            'event': {'storage'},
            'memory': {'storage', 'event'},
            'llm': {'config'},
            'runtime': {'event', 'memory'},
            'session': {'event', 'runtime', 'memory'}
        }
        
    def _get_initialization_order(self) -> List[str]:
        """Get correct service initialization order"""
        visited = set()
        order = []
        
        def visit(service: str):
            if service in visited:
                return
            visited.add(service)
            
            # Visit dependencies first
            for dep in self.dependencies[service]:
                visit(dep)
            order.append(service)
            
        for service in self.dependencies:
            visit(service)
            
        return order
        
    async def _initialize_service(self, name: str):
        """Initialize individual service"""
        logger.info(f"Initializing service: {name}")
        
        service_class = self._get_service_class(name)
        service = service_class(self.config)
        
        try:
            await service.initialize()
            self.services[name] = service
        except Exception as e:
            logger.error(f"Failed to initialize {name}: {e}")
            raise ServiceInitializationError(name, str(e))
```

### 4. Component Registration
```python
# File: openhands/core/registry.py

class ComponentRegistry:
    """Manages component registration"""
    
    def __init__(self):
        self.agents = {}
        self.capabilities = {}
        self.event_handlers = {}
        self.memory_providers = {}
        
    async def register_components(self):
        """Register all system components"""
        # 1. Register agents
        await self._register_agents()
        
        # 2. Register capabilities
        await self._register_capabilities()
        
        # 3. Register event handlers
        await self._register_event_handlers()
        
        # 4. Register memory providers
        await self._register_memory_providers()
        
    async def _register_agents(self):
        """Register available agents"""
        # Load agent modules
        agent_path = Path('openhands/agents')
        for module in agent_path.glob('*.py'):
            if module.stem.startswith('_'):
                continue
                
            # Import module
            spec = importlib.util.spec_from_file_location(
                module.stem,
                str(module)
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Register agents
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Agent) and
                    obj != Agent):
                    self.agents[name] = obj
```

### 5. Service Startup
```python
# File: openhands/server/app.py

class ApplicationServer:
    """Main application server"""
    
    def __init__(self, config: Config):
        self.config = config
        self.app = FastAPI()
        self.background_tasks = []
        
    async def start(self):
        """Start application server"""
        # 1. Initialize components
        await self._initialize_components()
        
        # 2. Setup routes
        self._setup_routes()
        
        # 3. Start background tasks
        await self._start_background_tasks()
        
        # 4. Start server
        await self._start_server()
        
    async def _initialize_components(self):
        """Initialize server components"""
        # Initialize session manager
        self.session_manager = SessionManager(self.config)
        await self.session_manager.initialize()
        
        # Initialize API components
        self.api = APIManager(self.config)
        await self.api.initialize()
        
    def _setup_routes(self):
        """Setup API routes"""
        # Add routers
        self.app.include_router(
            conversation_router,
            prefix="/api/v1/conversation",
            tags=["conversation"]
        )
        
        self.app.include_router(
            agent_router,
            prefix="/api/v1/agents",
            tags=["agents"]
        )
        
        self.app.include_router(
            system_router,
            prefix="/api/v1/system",
            tags=["system"]
        )
        
    async def _start_background_tasks(self):
        """Start background tasks"""
        # Add background tasks
        self.background_tasks.extend([
            asyncio.create_task(self._cleanup_task()),
            asyncio.create_task(self._monitor_task()),
            asyncio.create_task(self._maintenance_task())
        ])
```

## Key Initialization Points

1. **Configuration Dependencies**
   - Environment variables must be set before configuration loading
   - Configuration must be validated before service initialization
   - Service-specific configs are loaded after core configuration

2. **Service Dependencies**
   - Storage system must initialize first
   - Event system depends on storage
   - Memory system depends on storage and events
   - Runtime depends on events and memory
   - Session manager depends on all core services

3. **Component Registration**
   - Agents must be registered before session initialization
   - Capabilities must be registered before runtime initialization
   - Event handlers must be registered before event system start
   - Memory providers must be registered before memory system start

4. **Startup Order**
   - Core services must be initialized before component registration
   - Component registration must complete before service startup
   - Background tasks start after all components are initialized
   - Server starts only after all systems are ready

## Initialization Best Practices

1. **Error Handling**
   ```python
   try:
       await system.initialize()
   except ConfigurationError as e:
       logger.error(f"Configuration error: {e}")
       sys.exit(1)
   except ServiceInitializationError as e:
       logger.error(f"Service initialization failed: {e}")
       sys.exit(1)
   except ComponentRegistrationError as e:
       logger.error(f"Component registration failed: {e}")
       sys.exit(1)
   ```

2. **Health Checks**
   ```python
   async def check_system_health():
       """Verify system initialization"""
       # Check core services
       for service in service_manager.services.values():
           if not await service.is_healthy():
               return False
               
       # Check components
       for component in component_registry.components.values():
           if not await component.is_ready():
               return False
               
       return True
   ```

3. **Graceful Shutdown**
   ```python
   async def shutdown():
       """Graceful system shutdown"""
       # Stop background tasks
       for task in background_tasks:
           task.cancel()
           
       # Shutdown services in reverse order
       for service in reversed(service_manager.services.values()):
           await service.shutdown()
           
       # Close connections
       await storage.close()
       await event_system.close()
   ```

Remember:
- Always validate configuration before proceeding
- Initialize services in correct dependency order
- Handle initialization errors gracefully
- Perform health checks after initialization
- Implement proper shutdown procedures