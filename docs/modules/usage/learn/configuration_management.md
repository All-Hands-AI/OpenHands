# OpenHands Configuration Management Guide

This guide covers configuration management, environment handling, and settings management for OpenHands systems.

## Table of Contents
1. [Configuration System](#configuration-system)
2. [Environment Management](#environment-management)
3. [Feature Flags](#feature-flags)
4. [Settings Management](#settings-management)

## Configuration System

### 1. Configuration Manager

Implementation of configuration management system:

```python
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import json
import os
import re

class ConfigurationSource:
    """Base configuration source"""
    
    async def load(self) -> dict:
        """Load configuration data"""
        raise NotImplementedError
        
    async def save(self, data: dict):
        """Save configuration data"""
        raise NotImplementedError

class FileConfigurationSource(ConfigurationSource):
    """File-based configuration source"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    async def load(self) -> dict:
        """Load configuration from file"""
        if not self.file_path.exists():
            return {}
            
        with open(self.file_path) as f:
            if self.file_path.suffix == '.yaml':
                return yaml.safe_load(f)
            elif self.file_path.suffix == '.json':
                return json.load(f)
            else:
                raise ValueError(
                    f"Unsupported file type: {self.file_path.suffix}"
                )
                
    async def save(self, data: dict):
        """Save configuration to file"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.file_path, 'w') as f:
            if self.file_path.suffix == '.yaml':
                yaml.dump(data, f)
            elif self.file_path.suffix == '.json':
                json.dump(data, f, indent=2)
            else:
                raise ValueError(
                    f"Unsupported file type: {self.file_path.suffix}"
                )

class EnvironmentConfigurationSource(ConfigurationSource):
    """Environment variable configuration source"""
    
    def __init__(self, prefix: str = "OPENHANDS_"):
        self.prefix = prefix
        
    async def load(self) -> dict:
        """Load configuration from environment"""
        config = {}
        
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                config_key = self._parse_env_key(
                    key[len(self.prefix):]
                )
                config_value = self._parse_env_value(value)
                
                # Set nested configuration
                current = config
                parts = config_key.split('.')
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = config_value
                
        return config
        
    async def save(self, data: dict):
        """Save configuration to environment"""
        # Flatten configuration
        flat_config = self._flatten_dict(data)
        
        # Set environment variables
        for key, value in flat_config.items():
            env_key = f"{self.prefix}{key.upper()}"
            os.environ[env_key] = str(value)
            
    def _parse_env_key(self, key: str) -> str:
        """Parse environment key to config key"""
        # Convert KEY_NAME to key.name
        return key.lower().replace('_', '.')
        
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment value"""
        # Try to parse as JSON
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
            
    def _flatten_dict(
        self,
        d: dict,
        parent_key: str = ''
    ) -> dict:
        """Flatten nested dictionary"""
        items = []
        
        for k, v in d.items():
            new_key = f"{parent_key}_{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(
                    self._flatten_dict(v, new_key).items()
                )
            else:
                items.append((new_key, v))
                
        return dict(items)

class ConfigurationManager:
    """Configuration management system"""
    
    def __init__(self):
        self.sources: List[ConfigurationSource] = []
        self.config: Dict[str, Any] = {}
        self.watchers: Dict[str, List[Callable]] = {}
        
    def add_source(
        self,
        source: ConfigurationSource,
        priority: int = 0
    ):
        """Add configuration source"""
        self.sources.append((priority, source))
        # Sort sources by priority (highest first)
        self.sources.sort(key=lambda x: x[0], reverse=True)
        
    async def load(self):
        """Load configuration from all sources"""
        config = {}
        
        # Load from each source
        for _, source in self.sources:
            source_config = await source.load()
            self._deep_update(config, source_config)
            
        # Update configuration
        old_config = self.config.copy()
        self.config = config
        
        # Notify watchers
        await self._notify_watchers(old_config)
        
    async def save(self):
        """Save configuration to all sources"""
        for _, source in self.sources:
            await source.save(self.config)
            
    def get(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """Get configuration value"""
        return self._get_nested(self.config, key, default)
        
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self._set_nested(self.config, key, value)
        
    def watch(
        self,
        pattern: str,
        callback: Callable
    ):
        """Watch configuration changes"""
        if pattern not in self.watchers:
            self.watchers[pattern] = []
        self.watchers[pattern].append(callback)
        
    def _deep_update(
        self,
        d1: dict,
        d2: dict
    ):
        """Deep update dictionary"""
        for k, v in d2.items():
            if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
                self._deep_update(d1[k], v)
            else:
                d1[k] = v
                
    def _get_nested(
        self,
        d: dict,
        key: str,
        default: Any = None
    ) -> Any:
        """Get nested dictionary value"""
        parts = key.split('.')
        current = d
        
        for part in parts:
            if not isinstance(current, dict):
                return default
            if part not in current:
                return default
            current = current[part]
            
        return current
        
    def _set_nested(
        self,
        d: dict,
        key: str,
        value: Any
    ):
        """Set nested dictionary value"""
        parts = key.split('.')
        current = d
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
            
        current[parts[-1]] = value
        
    async def _notify_watchers(
        self,
        old_config: dict
    ):
        """Notify configuration watchers"""
        for pattern, callbacks in self.watchers.items():
            # Convert pattern to regex
            regex = re.compile(
                pattern.replace('.', r'\.').replace('*', r'.*')
            )
            
            # Find matching keys
            for key in self._get_all_keys(self.config):
                if regex.match(key):
                    old_value = self._get_nested(
                        old_config,
                        key
                    )
                    new_value = self._get_nested(
                        self.config,
                        key
                    )
                    
                    if old_value != new_value:
                        for callback in callbacks:
                            await callback(
                                key,
                                old_value,
                                new_value
                            )
```

## Environment Management

### 1. Environment Manager

Implementation of environment management:

```python
class Environment:
    """Environment configuration"""
    
    def __init__(
        self,
        name: str,
        config: dict
    ):
        self.name = name
        self.config = config
        self.active = False
        
    def activate(self):
        """Activate environment"""
        # Set environment variables
        for key, value in self.config.get('env', {}).items():
            os.environ[key] = str(value)
            
        # Set Python path
        python_path = self.config.get('python_path', [])
        if python_path:
            os.environ['PYTHONPATH'] = os.pathsep.join(
                python_path
            )
            
        self.active = True
        
    def deactivate(self):
        """Deactivate environment"""
        # Unset environment variables
        for key in self.config.get('env', {}):
            os.environ.pop(key, None)
            
        # Restore Python path
        os.environ.pop('PYTHONPATH', None)
        
        self.active = False

class EnvironmentManager:
    """Environment management system"""
    
    def __init__(self):
        self.environments: Dict[str, Environment] = {}
        self.active_environment: Optional[str] = None
        
    def add_environment(
        self,
        name: str,
        config: dict
    ):
        """Add environment configuration"""
        self.environments[name] = Environment(
            name,
            config
        )
        
    def activate_environment(self, name: str):
        """Activate environment"""
        if name not in self.environments:
            raise ValueError(
                f"Unknown environment: {name}"
            )
            
        # Deactivate current environment
        if self.active_environment:
            self.environments[
                self.active_environment
            ].deactivate()
            
        # Activate new environment
        self.environments[name].activate()
        self.active_environment = name
        
    def get_active_environment(self) -> Optional[str]:
        """Get active environment name"""
        return self.active_environment
```

## Feature Flags

### 1. Feature Flag System

Implementation of feature flag system:

```python
class FeatureFlag:
    """Feature flag definition"""
    
    def __init__(
        self,
        name: str,
        description: str,
        enabled: bool = False,
        conditions: Optional[dict] = None
    ):
        self.name = name
        self.description = description
        self.enabled = enabled
        self.conditions = conditions or {}
        
    def evaluate(self, context: dict) -> bool:
        """Evaluate feature flag"""
        if not self.enabled:
            return False
            
        # Check conditions
        for condition_type, condition in self.conditions.items():
            checker = FLAG_CONDITIONS.get(condition_type)
            if checker and not checker(condition, context):
                return False
                
        return True

class FeatureFlagManager:
    """Feature flag management system"""
    
    def __init__(self):
        self.flags: Dict[str, FeatureFlag] = {}
        
    def add_flag(
        self,
        name: str,
        description: str,
        enabled: bool = False,
        conditions: Optional[dict] = None
    ):
        """Add feature flag"""
        self.flags[name] = FeatureFlag(
            name,
            description,
            enabled,
            conditions
        )
        
    def is_enabled(
        self,
        flag_name: str,
        context: Optional[dict] = None
    ) -> bool:
        """Check if feature is enabled"""
        if flag_name not in self.flags:
            return False
            
        return self.flags[flag_name].evaluate(
            context or {}
        )
        
    def enable_flag(self, flag_name: str):
        """Enable feature flag"""
        if flag_name in self.flags:
            self.flags[flag_name].enabled = True
            
    def disable_flag(self, flag_name: str):
        """Disable feature flag"""
        if flag_name in self.flags:
            self.flags[flag_name].enabled = False
            
    def update_conditions(
        self,
        flag_name: str,
        conditions: dict
    ):
        """Update flag conditions"""
        if flag_name in self.flags:
            self.flags[flag_name].conditions = conditions

# Feature flag condition checkers
FLAG_CONDITIONS = {
    'environment': lambda c, ctx: ctx.get('environment') in c,
    'percentage': lambda c, ctx: hash(ctx.get('user_id', '')) % 100 < c,
    'date_range': lambda c, ctx: (
        datetime.now() >= datetime.fromisoformat(c['start'])
        and datetime.now() <= datetime.fromisoformat(c['end'])
    ),
    'user_group': lambda c, ctx: ctx.get('user_group') in c
}
```

## Settings Management

### 1. Settings Manager

Implementation of settings management:

```python
class Setting:
    """Setting definition"""
    
    def __init__(
        self,
        name: str,
        value_type: type,
        default_value: Any,
        description: str,
        validator: Optional[Callable] = None
    ):
        self.name = name
        self.value_type = value_type
        self.default_value = default_value
        self.description = description
        self.validator = validator
        self.value = default_value
        
    def validate(self, value: Any) -> bool:
        """Validate setting value"""
        # Check type
        if not isinstance(value, self.value_type):
            return False
            
        # Check custom validator
        if self.validator and not self.validator(value):
            return False
            
        return True
        
    def set_value(self, value: Any):
        """Set setting value"""
        if not self.validate(value):
            raise ValueError(
                f"Invalid value for setting {self.name}"
            )
        self.value = value
        
    def get_value(self) -> Any:
        """Get setting value"""
        return self.value

class SettingsManager:
    """Settings management system"""
    
    def __init__(self):
        self.settings: Dict[str, Setting] = {}
        self.watchers: Dict[str, List[Callable]] = {}
        
    def register_setting(
        self,
        name: str,
        value_type: type,
        default_value: Any,
        description: str,
        validator: Optional[Callable] = None
    ):
        """Register setting"""
        self.settings[name] = Setting(
            name,
            value_type,
            default_value,
            description,
            validator
        )
        
    def get_setting(
        self,
        name: str,
        default: Any = None
    ) -> Any:
        """Get setting value"""
        if name not in self.settings:
            return default
        return self.settings[name].get_value()
        
    def set_setting(
        self,
        name: str,
        value: Any
    ):
        """Set setting value"""
        if name not in self.settings:
            raise ValueError(f"Unknown setting: {name}")
            
        old_value = self.settings[name].get_value()
        self.settings[name].set_value(value)
        
        # Notify watchers
        self._notify_watchers(name, old_value, value)
        
    def watch_setting(
        self,
        name: str,
        callback: Callable
    ):
        """Watch setting changes"""
        if name not in self.watchers:
            self.watchers[name] = []
        self.watchers[name].append(callback)
        
    def _notify_watchers(
        self,
        name: str,
        old_value: Any,
        new_value: Any
    ):
        """Notify setting watchers"""
        if name in self.watchers:
            for callback in self.watchers[name]:
                callback(name, old_value, new_value)
```

Remember to:
- Handle configuration changes
- Validate settings
- Manage environments
- Control feature flags
- Monitor configuration
- Document settings
- Handle migrations