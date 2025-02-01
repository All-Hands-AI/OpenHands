# OpenHands Security Patterns Guide

This guide covers security patterns, access control, and authentication/authorization mechanisms for OpenHands systems.

## Table of Contents
1. [Authentication System](#authentication-system)
2. [Authorization System](#authorization-system)
3. [Security Middleware](#security-middleware)
4. [Encryption System](#encryption-system)

## Authentication System

### 1. Authentication Manager

Implementation of authentication system:

```python
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import jwt
import bcrypt
import secrets
import asyncio

class AuthenticationError(Exception):
    """Authentication error"""
    pass

class User:
    """User information"""
    
    def __init__(
        self,
        user_id: str,
        username: str,
        password_hash: str,
        roles: List[str] = None,
        metadata: dict = None
    ):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.roles = roles or []
        self.metadata = metadata or {}
        self.last_login = None
        self.failed_attempts = 0
        self.locked_until = None
        
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'roles': self.roles,
            'metadata': self.metadata,
            'last_login': self.last_login.isoformat()
                if self.last_login else None
        }

class AuthenticationManager:
    """Authentication management system"""
    
    def __init__(
        self,
        secret_key: str,
        token_expiry: int = 3600,
        max_attempts: int = 3,
        lockout_duration: int = 300
    ):
        self.secret_key = secret_key
        self.token_expiry = token_expiry
        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration
        self.users: Dict[str, User] = {}
        self.active_tokens: Dict[str, str] = {}
        
    async def register_user(
        self,
        username: str,
        password: str,
        roles: List[str] = None,
        metadata: dict = None
    ) -> User:
        """Register new user"""
        # Check if username exists
        if any(u.username == username
               for u in self.users.values()):
            raise AuthenticationError(
                "Username already exists"
            )
            
        # Create user
        user_id = secrets.token_urlsafe(16)
        password_hash = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        )
        
        user = User(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            roles=roles,
            metadata=metadata
        )
        
        self.users[user_id] = user
        return user
        
    async def authenticate(
        self,
        username: str,
        password: str
    ) -> str:
        """Authenticate user and return token"""
        # Find user
        user = next(
            (u for u in self.users.values()
             if u.username == username),
            None
        )
        
        if not user:
            raise AuthenticationError(
                "Invalid username or password"
            )
            
        # Check lockout
        if user.locked_until and datetime.now() < user.locked_until:
            raise AuthenticationError(
                "Account is locked"
            )
            
        # Verify password
        if not bcrypt.checkpw(
            password.encode(),
            user.password_hash
        ):
            user.failed_attempts += 1
            
            # Check lockout
            if user.failed_attempts >= self.max_attempts:
                user.locked_until = datetime.now() + timedelta(
                    seconds=self.lockout_duration
                )
                
            raise AuthenticationError(
                "Invalid username or password"
            )
            
        # Reset failed attempts
        user.failed_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now()
        
        # Generate token
        token = self._generate_token(user)
        self.active_tokens[token] = user.user_id
        
        return token
        
    async def validate_token(
        self,
        token: str
    ) -> Optional[User]:
        """Validate authentication token"""
        if token not in self.active_tokens:
            return None
            
        try:
            # Verify token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=['HS256']
            )
            
            # Check expiry
            if datetime.fromtimestamp(payload['exp']) < datetime.now():
                self._revoke_token(token)
                return None
                
            # Get user
            user_id = payload['sub']
            return self.users.get(user_id)
            
        except jwt.InvalidTokenError:
            self._revoke_token(token)
            return None
            
    async def revoke_token(self, token: str):
        """Revoke authentication token"""
        self._revoke_token(token)
        
    def _generate_token(self, user: User) -> str:
        """Generate authentication token"""
        payload = {
            'sub': user.user_id,
            'username': user.username,
            'roles': user.roles,
            'exp': datetime.now() + timedelta(
                seconds=self.token_expiry
            )
        }
        
        return jwt.encode(
            payload,
            self.secret_key,
            algorithm='HS256'
        )
        
    def _revoke_token(self, token: str):
        """Revoke token"""
        self.active_tokens.pop(token, None)
```

## Authorization System

### 1. Access Control

Implementation of access control system:

```python
from enum import Enum
from typing import Dict, Set, Optional

class Permission(Enum):
    """Permission types"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

class Resource:
    """Protected resource"""
    
    def __init__(
        self,
        resource_id: str,
        owner_id: str,
        resource_type: str
    ):
        self.resource_id = resource_id
        self.owner_id = owner_id
        self.resource_type = resource_type
        self.permissions: Dict[str, Set[Permission]] = {}
        
    def grant_permission(
        self,
        user_id: str,
        permission: Permission
    ):
        """Grant permission to user"""
        if user_id not in self.permissions:
            self.permissions[user_id] = set()
        self.permissions[user_id].add(permission)
        
    def revoke_permission(
        self,
        user_id: str,
        permission: Permission
    ):
        """Revoke permission from user"""
        if user_id in self.permissions:
            self.permissions[user_id].discard(permission)
            
    def has_permission(
        self,
        user_id: str,
        permission: Permission
    ) -> bool:
        """Check if user has permission"""
        return (user_id == self.owner_id or
                permission in self.permissions.get(user_id, set()))

class AccessControlList:
    """Access control list implementation"""
    
    def __init__(self):
        self.resources: Dict[str, Resource] = {}
        self.role_permissions: Dict[str, Set[Permission]] = {}
        
    def add_resource(
        self,
        resource: Resource
    ):
        """Add protected resource"""
        self.resources[resource.resource_id] = resource
        
    def remove_resource(
        self,
        resource_id: str
    ):
        """Remove protected resource"""
        self.resources.pop(resource_id, None)
        
    def set_role_permissions(
        self,
        role: str,
        permissions: Set[Permission]
    ):
        """Set permissions for role"""
        self.role_permissions[role] = permissions
        
    async def check_access(
        self,
        user: User,
        resource_id: str,
        permission: Permission
    ) -> bool:
        """Check access permission"""
        resource = self.resources.get(resource_id)
        if not resource:
            return False
            
        # Check direct permission
        if resource.has_permission(user.user_id, permission):
            return True
            
        # Check role permissions
        for role in user.roles:
            if permission in self.role_permissions.get(role, set()):
                return True
                
        return False
```

## Security Middleware

### 1. Security Layer

Implementation of security middleware:

```python
from fastapi import Request, HTTPException
from typing import Optional, Callable

class SecurityMiddleware:
    """Security middleware implementation"""
    
    def __init__(
        self,
        auth_manager: AuthenticationManager,
        acl: AccessControlList
    ):
        self.auth_manager = auth_manager
        self.acl = acl
        
    async def authenticate_request(
        self,
        request: Request
    ) -> Optional[User]:
        """Authenticate HTTP request"""
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
            
        # Parse token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
            
        token = parts[1]
        
        # Validate token
        return await self.auth_manager.validate_token(token)
        
    async def check_permission(
        self,
        user: User,
        resource_id: str,
        permission: Permission
    ) -> bool:
        """Check access permission"""
        return await self.acl.check_access(
            user,
            resource_id,
            permission
        )

def require_auth(
    security: SecurityMiddleware
) -> Callable:
    """Authentication requirement decorator"""
    
    async def decorator(
        request: Request
    ) -> User:
        user = await security.authenticate_request(request)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        return user
        
    return decorator

def require_permission(
    security: SecurityMiddleware,
    resource_id: str,
    permission: Permission
) -> Callable:
    """Permission requirement decorator"""
    
    async def decorator(
        request: Request,
        user: User = Depends(require_auth(security))
    ):
        if not await security.check_permission(
            user,
            resource_id,
            permission
        ):
            raise HTTPException(
                status_code=403,
                detail="Permission denied"
            )
        return user
        
    return decorator
```

## Encryption System

### 1. Data Encryption

Implementation of data encryption:

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class EncryptionManager:
    """Data encryption management"""
    
    def __init__(
        self,
        master_key: str,
        salt: Optional[bytes] = None
    ):
        self.master_key = master_key
        self.salt = salt or os.urandom(16)
        self.key = self._derive_key()
        self.fernet = Fernet(self.key)
        
    def _derive_key(self) -> bytes:
        """Derive encryption key"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000
        )
        
        key = base64.urlsafe_b64encode(
            kdf.derive(self.master_key.encode())
        )
        return key
        
    def encrypt(self, data: str) -> str:
        """Encrypt data"""
        return self.fernet.encrypt(
            data.encode()
        ).decode()
        
    def decrypt(self, encrypted: str) -> str:
        """Decrypt data"""
        return self.fernet.decrypt(
            encrypted.encode()
        ).decode()
        
    def rotate_key(self):
        """Rotate encryption key"""
        self.salt = os.urandom(16)
        self.key = self._derive_key()
        self.fernet = Fernet(self.key)

class SecureStorage:
    """Secure data storage"""
    
    def __init__(
        self,
        encryption: EncryptionManager
    ):
        self.encryption = encryption
        self.data: Dict[str, str] = {}
        
    async def store(
        self,
        key: str,
        value: str
    ):
        """Store encrypted data"""
        encrypted = self.encryption.encrypt(value)
        self.data[key] = encrypted
        
    async def retrieve(
        self,
        key: str
    ) -> Optional[str]:
        """Retrieve decrypted data"""
        encrypted = self.data.get(key)
        if not encrypted:
            return None
            
        return self.encryption.decrypt(encrypted)
        
    async def delete(
        self,
        key: str
    ):
        """Delete stored data"""
        self.data.pop(key, None)
```

Remember to:
- Implement proper authentication
- Manage access control
- Secure sensitive data
- Use encryption appropriately
- Handle security errors
- Monitor security events
- Document security measures