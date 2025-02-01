# OpenHands Data Management Guide

This guide covers data management, storage patterns, and data processing strategies for OpenHands systems.

## Table of Contents
1. [Data Storage Patterns](#data-storage-patterns)
2. [Data Processing Pipeline](#data-processing-pipeline)
3. [Data Versioning](#data-versioning)
4. [Data Migration](#data-migration)

## Data Storage Patterns

### 1. Storage Manager

Implementation of unified storage management:

```python
from enum import Enum
from typing import Dict, List, Any, Optional, BinaryIO
from pathlib import Path
import asyncio
import json
import aiofiles

class StorageType(Enum):
    LOCAL = "local"
    S3 = "s3"
    REDIS = "redis"
    POSTGRES = "postgres"

class StorageManager:
    """Unified storage management system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.adapters: Dict[StorageType, Any] = {}
        self.default_storage = StorageType.LOCAL
        
    async def initialize(self):
        """Initialize storage adapters"""
        for storage_config in self.config.get('storage', []):
            storage_type = StorageType(storage_config['type'])
            adapter = await self._create_adapter(
                storage_type,
                storage_config
            )
            self.adapters[storage_type] = adapter
            
    async def store_data(
        self,
        key: str,
        data: Any,
        storage_type: Optional[StorageType] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """Store data using specified storage"""
        storage_type = storage_type or self.default_storage
        adapter = self._get_adapter(storage_type)
        
        # Prepare metadata
        full_metadata = {
            'timestamp': datetime.now().isoformat(),
            'storage_type': storage_type.value,
            'content_type': self._get_content_type(data)
        }
        if metadata:
            full_metadata.update(metadata)
            
        # Store data
        location = await adapter.store(
            key,
            data,
            full_metadata
        )
        
        return location
        
    async def retrieve_data(
        self,
        key: str,
        storage_type: Optional[StorageType] = None
    ) -> Any:
        """Retrieve stored data"""
        storage_type = storage_type or self.default_storage
        adapter = self._get_adapter(storage_type)
        
        return await adapter.retrieve(key)
        
    async def delete_data(
        self,
        key: str,
        storage_type: Optional[StorageType] = None
    ):
        """Delete stored data"""
        storage_type = storage_type or self.default_storage
        adapter = self._get_adapter(storage_type)
        
        await adapter.delete(key)
        
    def _get_adapter(self, storage_type: StorageType) -> Any:
        """Get storage adapter"""
        if storage_type not in self.adapters:
            raise ValueError(
                f"Storage type not configured: {storage_type}"
            )
        return self.adapters[storage_type]
        
    async def _create_adapter(
        self,
        storage_type: StorageType,
        config: dict
    ) -> Any:
        """Create storage adapter"""
        if storage_type == StorageType.LOCAL:
            return LocalStorageAdapter(config)
        elif storage_type == StorageType.S3:
            return S3StorageAdapter(config)
        elif storage_type == StorageType.REDIS:
            return RedisStorageAdapter(config)
        elif storage_type == StorageType.POSTGRES:
            return PostgresStorageAdapter(config)
        else:
            raise ValueError(
                f"Unsupported storage type: {storage_type}"
            )
```

### 2. Storage Adapters

Implementation of storage adapters:

```python
class BaseStorageAdapter:
    """Base storage adapter"""
    
    def __init__(self, config: dict):
        self.config = config
        
    async def store(
        self,
        key: str,
        data: Any,
        metadata: dict
    ) -> str:
        """Store data"""
        raise NotImplementedError
        
    async def retrieve(self, key: str) -> Any:
        """Retrieve data"""
        raise NotImplementedError
        
    async def delete(self, key: str):
        """Delete data"""
        raise NotImplementedError

class LocalStorageAdapter(BaseStorageAdapter):
    """Local filesystem storage adapter"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.base_path = Path(config['path'])
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    async def store(
        self,
        key: str,
        data: Any,
        metadata: dict
    ) -> str:
        """Store data locally"""
        path = self.base_path / key
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Store data
        async with aiofiles.open(path, 'wb') as f:
            if isinstance(data, bytes):
                await f.write(data)
            elif isinstance(data, str):
                await f.write(data.encode())
            else:
                await f.write(
                    json.dumps(data).encode()
                )
                
        # Store metadata
        meta_path = path.with_suffix('.meta.json')
        async with aiofiles.open(meta_path, 'w') as f:
            await f.write(json.dumps(metadata))
            
        return str(path)
        
    async def retrieve(self, key: str) -> Any:
        """Retrieve local data"""
        path = self.base_path / key
        if not path.exists():
            raise FileNotFoundError(f"Data not found: {key}")
            
        # Get metadata
        meta_path = path.with_suffix('.meta.json')
        if meta_path.exists():
            async with aiofiles.open(meta_path, 'r') as f:
                metadata = json.loads(await f.read())
        else:
            metadata = {}
            
        # Read data
        async with aiofiles.open(path, 'rb') as f:
            data = await f.read()
            
        # Convert based on content type
        content_type = metadata.get('content_type', 'binary')
        if content_type == 'json':
            return json.loads(data)
        elif content_type == 'text':
            return data.decode()
        else:
            return data

class S3StorageAdapter(BaseStorageAdapter):
    """S3 storage adapter"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.bucket = config['bucket']
        self.client = boto3.client(
            's3',
            aws_access_key_id=config['access_key'],
            aws_secret_access_key=config['secret_key']
        )
        
    async def store(
        self,
        key: str,
        data: Any,
        metadata: dict
    ) -> str:
        """Store data in S3"""
        # Prepare data
        if isinstance(data, (dict, list)):
            body = json.dumps(data).encode()
            content_type = 'application/json'
        elif isinstance(data, str):
            body = data.encode()
            content_type = 'text/plain'
        else:
            body = data
            content_type = 'application/octet-stream'
            
        # Upload to S3
        await self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
            Metadata={
                k: str(v) for k, v in metadata.items()
            }
        )
        
        return f"s3://{self.bucket}/{key}"
```

## Data Processing Pipeline

### 1. Data Pipeline

Implementation of data processing pipeline:

```python
class DataProcessor:
    """Data processing pipeline"""
    
    def __init__(
        self,
        storage_manager: StorageManager
    ):
        self.storage_manager = storage_manager
        self.processors: List[Callable] = []
        self.validators: List[Callable] = []
        
    def add_processor(self, processor: Callable):
        """Add data processor"""
        self.processors.append(processor)
        
    def add_validator(self, validator: Callable):
        """Add data validator"""
        self.validators.append(validator)
        
    async def process_data(
        self,
        data: Any,
        metadata: Optional[dict] = None
    ) -> Any:
        """Process data through pipeline"""
        # Validate input
        for validator in self.validators:
            await validator(data)
            
        # Process data
        processed = data
        for processor in self.processors:
            processed = await processor(processed)
            
        return processed
        
    async def process_and_store(
        self,
        data: Any,
        key: str,
        metadata: Optional[dict] = None
    ) -> str:
        """Process and store data"""
        # Process data
        processed = await self.process_data(data)
        
        # Store processed data
        return await self.storage_manager.store_data(
            key,
            processed,
            metadata=metadata
        )

class DataTransformer:
    """Data transformation utilities"""
    
    @staticmethod
    async def normalize_text(text: str) -> str:
        """Normalize text data"""
        return text.strip().lower()
        
    @staticmethod
    async def validate_json(data: Any) -> bool:
        """Validate JSON data"""
        try:
            if isinstance(data, str):
                json.loads(data)
            else:
                json.dumps(data)
            return True
        except Exception:
            return False
```

## Data Versioning

### 1. Version Control

Implementation of data versioning:

```python
class DataVersion:
    """Data version information"""
    
    def __init__(
        self,
        version: str,
        location: str,
        metadata: dict
    ):
        self.version = version
        self.location = location
        self.metadata = metadata
        self.created_at = datetime.now()

class DataVersioning:
    """Data versioning system"""
    
    def __init__(
        self,
        storage_manager: StorageManager
    ):
        self.storage_manager = storage_manager
        self.versions: Dict[str, List[DataVersion]] = {}
        
    async def create_version(
        self,
        key: str,
        data: Any,
        metadata: Optional[dict] = None
    ) -> DataVersion:
        """Create new data version"""
        # Generate version
        version = self._generate_version(key)
        
        # Store data
        location = await self.storage_manager.store_data(
            f"{key}/{version}",
            data,
            metadata=metadata
        )
        
        # Create version info
        version_info = DataVersion(
            version=version,
            location=location,
            metadata=metadata or {}
        )
        
        # Store version info
        if key not in self.versions:
            self.versions[key] = []
        self.versions[key].append(version_info)
        
        return version_info
        
    async def get_version(
        self,
        key: str,
        version: Optional[str] = None
    ) -> Optional[DataVersion]:
        """Get specific version"""
        if key not in self.versions:
            return None
            
        if version:
            # Find specific version
            for ver in self.versions[key]:
                if ver.version == version:
                    return ver
            return None
        else:
            # Get latest version
            return self.versions[key][-1]
        
    async def get_version_data(
        self,
        key: str,
        version: Optional[str] = None
    ) -> Optional[Any]:
        """Get version data"""
        version_info = await self.get_version(key, version)
        if not version_info:
            return None
            
        return await self.storage_manager.retrieve_data(
            f"{key}/{version_info.version}"
        )
        
    def _generate_version(self, key: str) -> str:
        """Generate version string"""
        if key not in self.versions:
            return "v1"
            
        last_version = self.versions[key][-1].version
        version_num = int(last_version[1:])
        return f"v{version_num + 1}"
```

## Data Migration

### 1. Migration System

Implementation of data migration:

```python
class DataMigration:
    """Data migration system"""
    
    def __init__(
        self,
        storage_manager: StorageManager,
        versioning: DataVersioning
    ):
        self.storage_manager = storage_manager
        self.versioning = versioning
        self.migrations: Dict[str, List[dict]] = {}
        
    def register_migration(
        self,
        key: str,
        from_version: str,
        to_version: str,
        migrator: Callable
    ):
        """Register data migration"""
        if key not in self.migrations:
            self.migrations[key] = []
            
        self.migrations[key].append({
            'from_version': from_version,
            'to_version': to_version,
            'migrator': migrator
        })
        
    async def migrate_data(
        self,
        key: str,
        target_version: str
    ) -> DataVersion:
        """Migrate data to target version"""
        # Get current version
        current_version = await self.versioning.get_version(key)
        if not current_version:
            raise ValueError(f"No data found for key: {key}")
            
        # Find migration path
        path = self._find_migration_path(
            key,
            current_version.version,
            target_version
        )
        
        if not path:
            raise ValueError(
                f"No migration path found from "
                f"{current_version.version} to {target_version}"
            )
            
        # Execute migrations
        data = await self.versioning.get_version_data(key)
        
        for migration in path:
            data = await migration['migrator'](data)
            
            # Create new version
            current_version = await self.versioning.create_version(
                key,
                data,
                metadata={
                    'migrated_from': current_version.version,
                    'migration_type': migration['type']
                }
            )
            
        return current_version
        
    def _find_migration_path(
        self,
        key: str,
        from_version: str,
        to_version: str
    ) -> Optional[List[dict]]:
        """Find migration path between versions"""
        if key not in self.migrations:
            return None
            
        # Implement path finding algorithm
        # (e.g., using graph traversal)
        pass
```

Remember to:
- Implement proper data validation
- Handle versioning carefully
- Manage storage efficiently
- Document data structures
- Implement backup strategies
- Monitor storage usage
- Handle migration errors