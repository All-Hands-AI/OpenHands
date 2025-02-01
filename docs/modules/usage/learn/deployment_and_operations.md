# OpenHands Deployment and Operations Guide

This guide covers deployment strategies, operational considerations, and maintenance procedures for OpenHands systems.

## Table of Contents
1. [Deployment Strategies](#deployment-strategies)
2. [Configuration Management](#configuration-management)
3. [Monitoring and Logging](#monitoring-and-logging)
4. [Scaling and Performance](#scaling-and-performance)
5. [Maintenance and Updates](#maintenance-and-updates)

## Deployment Strategies

### 1. Docker Deployment

Using Docker for deployment provides consistency and isolation:

```dockerfile
# Dockerfile for OpenHands
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY openhands/ ./openhands/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Copy configuration
COPY config.toml ./

# Expose ports
EXPOSE 3000

# Start the application
CMD ["poetry", "run", "python", "-m", "openhands.server.listen"]
```

Docker Compose configuration for full stack deployment:

```yaml
# docker-compose.yml
version: '3.8'

services:
  openhands:
    build: .
    ports:
      - "3000:3000"
    volumes:
      - ./workspace:/app/workspace
    environment:
      - OPENHANDS_CONFIG=/app/config.toml
      - OPENHANDS_LOG_LEVEL=INFO
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:13
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=openhands
      - POSTGRES_PASSWORD=secret
      - POSTGRES_DB=openhands
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  redis_data:
  postgres_data:
```

### 2. Kubernetes Deployment

Example Kubernetes manifests for deploying OpenHands:

```yaml
# openhands-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openhands
spec:
  replicas: 3
  selector:
    matchLabels:
      app: openhands
  template:
    metadata:
      labels:
        app: openhands
    spec:
      containers:
      - name: openhands
        image: openhands:latest
        ports:
        - containerPort: 3000
        env:
        - name: OPENHANDS_CONFIG
          value: /app/config.toml
        - name: OPENHANDS_LOG_LEVEL
          value: INFO
        volumeMounts:
        - name: config
          mountPath: /app/config.toml
          subPath: config.toml
        - name: workspace
          mountPath: /app/workspace
      volumes:
      - name: config
        configMap:
          name: openhands-config
      - name: workspace
        persistentVolumeClaim:
          claimName: openhands-workspace

---
# openhands-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: openhands
spec:
  selector:
    app: openhands
  ports:
  - port: 80
    targetPort: 3000
  type: LoadBalancer
```

## Configuration Management

### 1. Configuration System

Example of a configuration management system:

```python
from pydantic import BaseModel
from typing import Dict, Any
import yaml
import os

class OpenHandsConfig(BaseModel):
    """Configuration model for OpenHands"""
    class ServerConfig(BaseModel):
        host: str = "0.0.0.0"
        port: int = 3000
        workers: int = 4
        
    class SecurityConfig(BaseModel):
        enable_auth: bool = True
        jwt_secret: str
        token_expiry: int = 3600
        
    class StorageConfig(BaseModel):
        type: str = "local"
        path: str = "./workspace"
        
    server: ServerConfig
    security: SecurityConfig
    storage: StorageConfig
    
    @classmethod
    def load(cls, path: str) -> 'OpenHandsConfig':
        """Load configuration from file"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
            
        with open(path) as f:
            config_data = yaml.safe_load(f)
            
        # Override with environment variables
        config_data = cls._override_from_env(config_data)
        return cls(**config_data)
    
    @staticmethod
    def _override_from_env(config: Dict[str, Any]) -> Dict[str, Any]:
        """Override configuration with environment variables"""
        env_prefix = "OPENHANDS_"
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                nested_keys = config_key.split('_')
                
                # Navigate to the correct nested dictionary
                current = config
                for k in nested_keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                
                # Set the value
                current[nested_keys[-1]] = value
                
        return config
```

### 2. Secret Management

Example of a secret management system:

```python
from cryptography.fernet import Fernet
import base64
import os

class SecretManager:
    def __init__(self, key_path: str = None):
        self.key = self._load_or_generate_key(key_path)
        self.fernet = Fernet(self.key)
        
    def _load_or_generate_key(self, key_path: str) -> bytes:
        """Load or generate encryption key"""
        if key_path and os.path.exists(key_path):
            with open(key_path, 'rb') as f:
                return base64.urlsafe_b64decode(f.read())
        
        # Generate new key
        key = Fernet.generate_key()
        if key_path:
            with open(key_path, 'wb') as f:
                f.write(base64.urlsafe_b64encode(key))
        return key
        
    def encrypt(self, value: str) -> str:
        """Encrypt a value"""
        return self.fernet.encrypt(value.encode()).decode()
        
    def decrypt(self, encrypted: str) -> str:
        """Decrypt a value"""
        return self.fernet.decrypt(encrypted.encode()).decode()
```

## Monitoring and Logging

### 1. Monitoring System

Example of a monitoring system:

```python
from dataclasses import dataclass
from datetime import datetime
import asyncio
import psutil

@dataclass
class SystemMetrics:
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    network_io: dict
    timestamp: datetime

class SystemMonitor:
    def __init__(self, interval: int = 60):
        self.interval = interval
        self.metrics_history = []
        self._running = False
        
    async def start(self):
        """Start monitoring"""
        self._running = True
        while self._running:
            metrics = self._collect_metrics()
            self.metrics_history.append(metrics)
            
            # Keep last 24 hours of metrics
            if len(self.metrics_history) > (24 * 60 * 60 / self.interval):
                self.metrics_history.pop(0)
                
            await asyncio.sleep(self.interval)
            
    def stop(self):
        """Stop monitoring"""
        self._running = False
        
    def _collect_metrics(self) -> SystemMetrics:
        """Collect system metrics"""
        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            disk_usage=psutil.disk_usage('/').percent,
            network_io=psutil.net_io_counters()._asdict(),
            timestamp=datetime.now()
        )
        
    def get_metrics(self, minutes: int = 5) -> list[SystemMetrics]:
        """Get recent metrics"""
        points = int(minutes * 60 / self.interval)
        return self.metrics_history[-points:]
```

### 2. Logging System

Example of a structured logging system:

```python
import logging
import json
from datetime import datetime
from typing import Any

class StructuredLogger:
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level))
        
        # Add JSON handler
        handler = logging.StreamHandler()
        handler.setFormatter(self.JsonFormatter())
        self.logger.addHandler(handler)
        
    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            """Format log record as JSON"""
            data = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            
            # Add extra fields
            if hasattr(record, 'extra'):
                data.update(record.extra)
                
            return json.dumps(data)
            
    def log(self, level: str, message: str, **kwargs):
        """Log a message with extra fields"""
        logger_func = getattr(self.logger, level.lower())
        logger_func(message, extra=kwargs)
```

## Scaling and Performance

### 1. Load Balancing

Example of implementing load balancing:

```python
from typing import List
import random
import asyncio

class LoadBalancer:
    def __init__(self, backends: List[str]):
        self.backends = backends
        self.active_backends = backends.copy()
        self.health_checks = {}
        
    async def get_backend(self) -> str:
        """Get next available backend"""
        if not self.active_backends:
            raise RuntimeError("No backends available")
            
        return random.choice(self.active_backends)
        
    async def start_health_checks(self):
        """Start health check loop"""
        for backend in self.backends:
            self.health_checks[backend] = asyncio.create_task(
                self._health_check_loop(backend)
            )
            
    async def _health_check_loop(self, backend: str):
        """Continuously check backend health"""
        while True:
            try:
                healthy = await self._check_health(backend)
                if healthy and backend not in self.active_backends:
                    self.active_backends.append(backend)
                elif not healthy and backend in self.active_backends:
                    self.active_backends.remove(backend)
            except Exception as e:
                logger.error(f"Health check failed for {backend}: {e}")
                
            await asyncio.sleep(30)  # Check every 30 seconds
            
    async def _check_health(self, backend: str) -> bool:
        """Check if backend is healthy"""
        try:
            # Implement health check logic
            return True
        except Exception:
            return False
```

### 2. Caching System

Example of implementing caching:

```python
from typing import Any, Optional
import time
import asyncio

class Cache:
    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self.data = {}
        self.locks = {}
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.data:
            return None
            
        value, expiry = self.data[key]
        if time.time() > expiry:
            del self.data[key]
            return None
            
        return value
        
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """Set value in cache"""
        expiry = time.time() + (ttl or self.ttl)
        self.data[key] = (value, expiry)
        
    async def get_or_set(
        self,
        key: str,
        factory: callable,
        ttl: Optional[int] = None
    ) -> Any:
        """Get value or create if missing"""
        # Check cache first
        value = await self.get(key)
        if value is not None:
            return value
            
        # Get or create lock
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
            
        # Double-checked locking pattern
        async with self.locks[key]:
            value = await self.get(key)
            if value is not None:
                return value
                
            # Create new value
            value = await factory()
            await self.set(key, value, ttl)
            return value
```

## Maintenance and Updates

### 1. Database Migrations

Example of a database migration system:

```python
from typing import List
import asyncpg
import yaml
from datetime import datetime

class Migration:
    def __init__(self, version: int, description: str, up: str, down: str):
        self.version = version
        self.description = description
        self.up = up
        self.down = down

class MigrationManager:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.migrations: List[Migration] = []
        
    async def init_migrations_table(self):
        """Initialize migrations table"""
        async with asyncpg.create_pool(self.db_url) as pool:
            async with pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS migrations (
                        version INTEGER PRIMARY KEY,
                        description TEXT,
                        applied_at TIMESTAMP WITH TIME ZONE
                    )
                """)
                
    def load_migrations(self, path: str):
        """Load migrations from YAML file"""
        with open(path) as f:
            data = yaml.safe_load(f)
            
        for migration in data['migrations']:
            self.migrations.append(Migration(
                version=migration['version'],
                description=migration['description'],
                up=migration['up'],
                down=migration['down']
            ))
            
    async def get_applied_versions(self) -> List[int]:
        """Get list of applied migration versions"""
        async with asyncpg.create_pool(self.db_url) as pool:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT version FROM migrations ORDER BY version"
                )
                return [row['version'] for row in rows]
                
    async def apply_migrations(self, target_version: Optional[int] = None):
        """Apply pending migrations"""
        applied = await self.get_applied_versions()
        
        for migration in sorted(
            self.migrations,
            key=lambda m: m.version
        ):
            if migration.version in applied:
                continue
                
            if target_version and migration.version > target_version:
                break
                
            await self._apply_migration(migration)
                
    async def _apply_migration(self, migration: Migration):
        """Apply a single migration"""
        async with asyncpg.create_pool(self.db_url) as pool:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(migration.up)
                    await conn.execute("""
                        INSERT INTO migrations (
                            version,
                            description,
                            applied_at
                        ) VALUES ($1, $2, $3)
                    """, migration.version, migration.description, datetime.now())
```

### 2. Backup System

Example of a backup system:

```python
import tarfile
import os
from datetime import datetime
import asyncio
import aioboto3

class BackupManager:
    def __init__(
        self,
        backup_dir: str,
        s3_bucket: str,
        aws_access_key: str,
        aws_secret_key: str
    ):
        self.backup_dir = backup_dir
        self.s3_bucket = s3_bucket
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        
    async def create_backup(self) -> str:
        """Create a backup archive"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"backup_{timestamp}.tar.gz"
        backup_path = os.path.join(self.backup_dir, backup_file)
        
        # Create tar archive
        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add("workspace", arcname="workspace")
            tar.add("config.toml", arcname="config.toml")
            
        return backup_path
        
    async def upload_to_s3(self, file_path: str):
        """Upload backup to S3"""
        session = aioboto3.Session(
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key
        )
        
        async with session.client('s3') as s3:
            filename = os.path.basename(file_path)
            await s3.upload_file(
                file_path,
                self.s3_bucket,
                f"backups/{filename}"
            )
            
    async def perform_backup(self):
        """Perform complete backup process"""
        try:
            # Create local backup
            backup_path = await self.create_backup()
            
            # Upload to S3
            await self.upload_to_s3(backup_path)
            
            # Cleanup local backup
            os.remove(backup_path)
            
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
```

Remember to:
- Implement proper error handling
- Add monitoring and logging
- Use appropriate security measures
- Test deployment procedures
- Document operational procedures
- Plan for scaling and maintenance
- Implement backup and recovery procedures