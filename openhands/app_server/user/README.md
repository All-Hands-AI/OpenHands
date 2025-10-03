# User Management

Handles user authentication, authorization, and profile management for the OpenHands app server.

## Overview

This module provides user management capabilities, including authentication, user profile access, and service resolution for user-scoped operations.

## Key Components

- **UserService**: Abstract service for user operations
- **LegacyUserService**: Compatibility layer for legacy user systems
- **UserRouter**: FastAPI router for user-related endpoints
- **UserServiceManager**: Factory for creating user-scoped service instances

## Features

- User authentication and session management
- Current user profile retrieval
- User-scoped service resolution
- JWT-based authentication integration
