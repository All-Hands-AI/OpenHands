# Conversation Management

Manages sandboxed conversations and their lifecycle within the OpenHands app server.

## Overview

This module provides services and models for managing conversations that run within sandboxed environments. It handles conversation creation, retrieval, status tracking, and lifecycle management.

## Key Components

- **SandboxedConversationService**: Abstract service for conversation CRUD operations
- **LiveStatusSandboxedConversationService**: Real-time conversation status tracking
- **SandboxedConversationRouter**: FastAPI router for conversation endpoints

## Features

- Conversation search and filtering by title, dates, and status
- Real-time conversation status updates
- Pagination support for large conversation lists
- Integration with sandbox environments
