# OpenHands Plugin System Guide

This guide covers plugin systems, extensibility frameworks, and modular architecture patterns for OpenHands systems.

## Table of Contents
1. [Plugin Framework](#plugin-framework)
2. [Extension Points](#extension-points)
3. [Module Loading](#module-loading)
4. [Plugin Management](#plugin-management)

## Plugin Framework

### 1. Plugin Base System

Implementation of core plugin framework:

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type
import importlib
import inspect
import pkgutil
import sys

class PluginMetadata:
    """Plugin metadata information"""
    
    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        author: str,
        dependencies: List[str] = None,
        entry_point: str = None
    ):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.dependencies = dependencies or []
        self.entry_point = entry_point

class Plugin(ABC):
    """Base plugin class"""
    
    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata
        self.initialized = False
        
    @abstractmethod
    async def initialize(self, context: dict):
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
        
    @property
    def name(self) -> str:
        """Get plugin name"""
        return self.metadata.name
        
    @property
    def version(self) -> str:
        """Get plugin version"""
        return self.metadata.version

class PluginManager:
    """Plugin management system"""
    
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.capabilities: Dict[str, List[str]] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        self.extension_points: Dict[str, Type] = {}
        
    async def load_plugin(
        self,
        plugin: Plugin,
        context: Optional[dict] = None
    ):
        """Load and initialize plugin"""
        # Check dependencies
        await self._check_dependencies(plugin)
        
        # Initialize plugin
        await plugin.initialize(context or {})
        plugin.initialized = True
        
        # Register plugin
        self.plugins[plugin.name] = plugin
        
        # Register capabilities
        for capability in plugin.capabilities:
            if capability not in self.capabilities:
                self.capabilities[capability] = []
            self.capabilities[capability].append(plugin.name)
            
    async def unload_plugin(self, name: str):
        """Unload plugin"""
        if name not in self.plugins:
            return
            
        plugin = self.plugins[name]
        
        # Cleanup plugin
        await plugin.cleanup()
        
        # Remove capabilities
        for capability, plugins in self.capabilities.items():
            if name in plugins:
                plugins.remove(name)
                
        # Remove plugin
        del self.plugins[name]
        
    def register_hook(
        self,
        hook_name: str,
        callback: Callable
    ):
        """Register plugin hook"""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(callback)
        
    async def execute_hook(
        self,
        hook_name: str,
        *args,
        **kwargs
    ) -> List[Any]:
        """Execute plugin hook"""
        results = []
        
        if hook_name in self.hooks:
            for callback in self.hooks[hook_name]:
                try:
                    result = await callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    logger.error(
                        f"Hook execution error: {e}"
                    )
                    
        return results
        
    def register_extension_point(
        self,
        name: str,
        base_class: Type
    ):
        """Register extension point"""
        self.extension_points[name] = base_class
        
    def get_extensions(
        self,
        extension_point: str
    ) -> List[Type]:
        """Get extensions for extension point"""
        if extension_point not in self.extension_points:
            return []
            
        base_class = self.extension_points[extension_point]
        return [
            cls for cls in base_class.__subclasses__()
            if cls.__module__ in self.plugins
        ]
        
    async def _check_dependencies(self, plugin: Plugin):
        """Check plugin dependencies"""
        for dependency in plugin.metadata.dependencies:
            if dependency not in self.plugins:
                raise ValueError(
                    f"Missing dependency: {dependency}"
                )
```

### 2. Plugin Discovery

Implementation of plugin discovery system:

```python
class PluginDiscovery:
    """Plugin discovery system"""
    
    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager
        self.search_paths: List[str] = []
        
    def add_search_path(self, path: str):
        """Add plugin search path"""
        if path not in self.search_paths:
            self.search_paths.append(path)
            
    async def discover_plugins(self) -> List[Plugin]:
        """Discover available plugins"""
        discovered = []
        
        for path in self.search_paths:
            # Add path to Python path
            if path not in sys.path:
                sys.path.append(path)
                
            # Search for plugin modules
            for _, name, _ in pkgutil.iter_modules([path]):
                try:
                    # Import module
                    module = importlib.import_module(name)
                    
                    # Find plugin classes
                    for item_name, item in inspect.getmembers(
                        module,
                        inspect.isclass
                    ):
                        if (issubclass(item, Plugin) and
                            item is not Plugin):
                            # Create plugin instance
                            metadata = self._get_plugin_metadata(
                                module,
                                item
                            )
                            plugin = item(metadata)
                            discovered.append(plugin)
                            
                except Exception as e:
                    logger.error(
                        f"Plugin discovery error: {e}"
                    )
                    
        return discovered
        
    def _get_plugin_metadata(
        self,
        module: Any,
        plugin_class: Type
    ) -> PluginMetadata:
        """Get plugin metadata"""
        return PluginMetadata(
            name=getattr(
                plugin_class,
                'PLUGIN_NAME',
                plugin_class.__name__
            ),
            version=getattr(
                plugin_class,
                'PLUGIN_VERSION',
                '0.1.0'
            ),
            description=getattr(
                plugin_class,
                'PLUGIN_DESCRIPTION',
                ''
            ),
            author=getattr(
                plugin_class,
                'PLUGIN_AUTHOR',
                'Unknown'
            ),
            dependencies=getattr(
                plugin_class,
                'PLUGIN_DEPENDENCIES',
                []
            ),
            entry_point=getattr(
                plugin_class,
                'PLUGIN_ENTRY_POINT',
                None
            )
        )
```

## Extension Points

### 1. Extension System

Implementation of extension point system:

```python
class ExtensionPoint(ABC):
    """Base extension point"""
    
    @abstractmethod
    def get_name(self) -> str:
        """Get extension point name"""
        pass
        
    @abstractmethod
    def get_interface(self) -> Type:
        """Get extension point interface"""
        pass

class Extension(ABC):
    """Base extension class"""
    
    @abstractmethod
    def get_extension_point(self) -> str:
        """Get extension point name"""
        pass

class ExtensionRegistry:
    """Extension registry system"""
    
    def __init__(self):
        self.extension_points: Dict[str, ExtensionPoint] = {}
        self.extensions: Dict[str, List[Extension]] = {}
        
    def register_extension_point(
        self,
        extension_point: ExtensionPoint
    ):
        """Register extension point"""
        name = extension_point.get_name()
        self.extension_points[name] = extension_point
        self.extensions[name] = []
        
    def register_extension(
        self,
        extension: Extension
    ):
        """Register extension"""
        point_name = extension.get_extension_point()
        
        if point_name not in self.extension_points:
            raise ValueError(
                f"Unknown extension point: {point_name}"
            )
            
        # Validate extension
        interface = self.extension_points[
            point_name
        ].get_interface()
        
        if not isinstance(extension, interface):
            raise ValueError(
                f"Extension does not implement interface: {interface}"
            )
            
        self.extensions[point_name].append(extension)
        
    def get_extensions(
        self,
        extension_point: str
    ) -> List[Extension]:
        """Get extensions for point"""
        return self.extensions.get(extension_point, [])
```

## Module Loading

### 1. Module System

Implementation of module loading system:

```python
class ModuleSpec:
    """Module specification"""
    
    def __init__(
        self,
        name: str,
        path: str,
        dependencies: List[str] = None
    ):
        self.name = name
        self.path = path
        self.dependencies = dependencies or []

class ModuleLoader:
    """Module loading system"""
    
    def __init__(self):
        self.loaded_modules: Dict[str, Any] = {}
        self.module_specs: Dict[str, ModuleSpec] = {}
        
    def register_module(
        self,
        spec: ModuleSpec
    ):
        """Register module specification"""
        self.module_specs[spec.name] = spec
        
    async def load_module(
        self,
        name: str
    ) -> Any:
        """Load module"""
        if name in self.loaded_modules:
            return self.loaded_modules[name]
            
        if name not in self.module_specs:
            raise ValueError(f"Unknown module: {name}")
            
        spec = self.module_specs[name]
        
        # Load dependencies
        for dependency in spec.dependencies:
            await self.load_module(dependency)
            
        # Load module
        try:
            module = importlib.import_module(spec.path)
            self.loaded_modules[name] = module
            return module
        except Exception as e:
            raise ValueError(
                f"Failed to load module {name}: {e}"
            )
            
    async def unload_module(
        self,
        name: str
    ):
        """Unload module"""
        if name not in self.loaded_modules:
            return
            
        # Check for dependent modules
        dependents = [
            mod_name for mod_name, spec
            in self.module_specs.items()
            if name in spec.dependencies
        ]
        
        if dependents:
            raise ValueError(
                f"Module {name} has dependents: {dependents}"
            )
            
        # Unload module
        if hasattr(self.loaded_modules[name], 'cleanup'):
            await self.loaded_modules[name].cleanup()
            
        del self.loaded_modules[name]
        
        # Remove from sys.modules
        if spec.path in sys.modules:
            del sys.modules[spec.path]
```

## Plugin Management

### 1. Plugin Registry

Implementation of plugin registry:

```python
class PluginRegistry:
    """Plugin registry system"""
    
    def __init__(self):
        self.plugins: Dict[str, PluginMetadata] = {}
        self.plugin_paths: Dict[str, str] = {}
        self.enabled_plugins: Set[str] = set()
        
    def register_plugin(
        self,
        metadata: PluginMetadata,
        path: str
    ):
        """Register plugin"""
        self.plugins[metadata.name] = metadata
        self.plugin_paths[metadata.name] = path
        
    def enable_plugin(self, name: str):
        """Enable plugin"""
        if name not in self.plugins:
            raise ValueError(f"Unknown plugin: {name}")
        self.enabled_plugins.add(name)
        
    def disable_plugin(self, name: str):
        """Disable plugin"""
        self.enabled_plugins.discard(name)
        
    def is_enabled(self, name: str) -> bool:
        """Check if plugin is enabled"""
        return name in self.enabled_plugins
        
    def get_enabled_plugins(self) -> List[str]:
        """Get enabled plugins"""
        return list(self.enabled_plugins)
        
    def get_plugin_info(
        self,
        name: str
    ) -> Optional[PluginMetadata]:
        """Get plugin information"""
        return self.plugins.get(name)
        
    def get_plugin_path(
        self,
        name: str
    ) -> Optional[str]:
        """Get plugin path"""
        return self.plugin_paths.get(name)
```

### 2. Plugin Configuration

Implementation of plugin configuration:

```python
class PluginConfig:
    """Plugin configuration"""
    
    def __init__(
        self,
        plugin_name: str,
        config: dict
    ):
        self.plugin_name = plugin_name
        self.config = config
        self.validators: Dict[str, Callable] = {}
        
    def get(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
        
    def set(
        self,
        key: str,
        value: Any
    ):
        """Set configuration value"""
        if key in self.validators:
            if not self.validators[key](value):
                raise ValueError(
                    f"Invalid value for {key}"
                )
        self.config[key] = value
        
    def register_validator(
        self,
        key: str,
        validator: Callable
    ):
        """Register configuration validator"""
        self.validators[key] = validator

class PluginConfigManager:
    """Plugin configuration manager"""
    
    def __init__(self):
        self.configs: Dict[str, PluginConfig] = {}
        
    def load_config(
        self,
        plugin_name: str,
        config_path: str
    ):
        """Load plugin configuration"""
        with open(config_path) as f:
            config = yaml.safe_load(f)
            
        self.configs[plugin_name] = PluginConfig(
            plugin_name,
            config
        )
        
    def get_config(
        self,
        plugin_name: str
    ) -> Optional[PluginConfig]:
        """Get plugin configuration"""
        return self.configs.get(plugin_name)
        
    def save_config(
        self,
        plugin_name: str,
        config_path: str
    ):
        """Save plugin configuration"""
        if plugin_name not in self.configs:
            return
            
        config = self.configs[plugin_name]
        with open(config_path, 'w') as f:
            yaml.dump(config.config, f)
```

Remember to:
- Document plugin interfaces
- Handle plugin dependencies
- Manage plugin lifecycle
- Validate plugin configurations
- Monitor plugin health
- Handle plugin updates
- Document extension points