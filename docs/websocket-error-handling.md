# WebSocket Error Handling Guide

This document provides guidance for handling WebSocket errors in OpenHands client applications.

## Error Response Format

All WebSocket errors are emitted as `oh_error` events with a standardized format:

```json
{
  "error_code": "WS_AUTH_1001",
  "message": "Authentication failed",
  "severity": "high",
  "timestamp": 1234567890.123,
  "correlation_id": "abc123-def456-ghi789",
  "retry_info": {
    "should_retry": false,
    "retry_after_seconds": null,
    "max_retries": null,
    "backoff_strategy": null
  },
  "details": {
    "reason": "invalid_token",
    "additional_context": "..."
  },
  "help_url": "/docs/troubleshooting/authentication"
}
```

## Error Code Categories

### Authentication Errors (1001-1099)
- `WS_AUTH_1001`: Authentication failed
- `WS_AUTH_1002`: Invalid session key
- `WS_AUTH_1003`: Session expired
- `WS_AUTH_1004`: Authorization denied

### Connection Errors (1101-1199)
- `WS_CONN_1101`: Connection refused
- `WS_CONN_1102`: Connection timeout
- `WS_CONN_1103`: Connection limit exceeded
- `WS_CONN_1104`: Invalid connection parameters

### Event Processing Errors (1201-1299)
- `WS_EVENT_1201`: Invalid event format
- `WS_EVENT_1202`: Event processing failed
- `WS_EVENT_1203`: Unsupported event type
- `WS_EVENT_1204`: Event validation failed

### Conversation Errors (1301-1399)
- `WS_CONV_1301`: Conversation not found
- `WS_CONV_1302`: Conversation access denied
- `WS_CONV_1303`: Conversation locked
- `WS_CONV_1304`: Invalid conversation state

### System Errors (1401-1499)
- `WS_SYS_1401`: Internal server error
- `WS_SYS_1402`: Service unavailable
- `WS_SYS_1403`: Rate limit exceeded
- `WS_SYS_1404`: Resource exhausted

### Client Errors (1501-1599)
- `WS_CLIENT_1501`: Invalid request
- `WS_CLIENT_1502`: Malformed data
- `WS_CLIENT_1503`: Protocol violation
- `WS_CLIENT_1504`: Client version unsupported

## Client Implementation Examples

### JavaScript/TypeScript

```typescript
interface WebSocketError {
  error_code: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: number;
  correlation_id?: string;
  retry_info?: {
    should_retry: boolean;
    retry_after_seconds?: number;
    max_retries?: number;
    backoff_strategy?: 'linear' | 'exponential' | 'fixed';
  };
  details?: Record<string, any>;
  help_url?: string;
}

class WebSocketErrorHandler {
  private retryAttempts = new Map<string, number>();

  handleError(error: WebSocketError): void {
    console.error(`WebSocket Error [${error.error_code}]: ${error.message}`, error);

    switch (error.severity) {
      case 'critical':
        this.handleCriticalError(error);
        break;
      case 'high':
        this.handleHighSeverityError(error);
        break;
      case 'medium':
        this.handleMediumSeverityError(error);
        break;
      case 'low':
        this.handleLowSeverityError(error);
        break;
    }

    if (error.retry_info?.should_retry) {
      this.scheduleRetry(error);
    }
  }

  private handleCriticalError(error: WebSocketError): void {
    // Show user-facing error message
    this.showErrorToUser(error.message, 'error');

    // Log for debugging
    this.logError(error);

    // Potentially redirect to error page or disable functionality
    if (error.error_code === 'WS_SYS_1401') {
      this.disableWebSocketFeatures();
    }
  }

  private handleAuthenticationError(error: WebSocketError): void {
    // Clear stored credentials
    this.clearAuthTokens();

    // Redirect to login
    this.redirectToLogin();

    // Show authentication error message
    this.showErrorToUser('Please log in again', 'warning');
  }

  private scheduleRetry(error: WebSocketError): void {
    if (!error.retry_info?.should_retry) return;

    const attemptKey = error.correlation_id || error.error_code;
    const currentAttempts = this.retryAttempts.get(attemptKey) || 0;

    if (error.retry_info.max_retries && currentAttempts >= error.retry_info.max_retries) {
      console.warn(`Max retry attempts reached for ${error.error_code}`);
      return;
    }

    const delay = this.calculateRetryDelay(error.retry_info, currentAttempts);

    setTimeout(() => {
      this.retryAttempts.set(attemptKey, currentAttempts + 1);
      this.attemptReconnection();
    }, delay * 1000);
  }

  private calculateRetryDelay(retryInfo: any, attempt: number): number {
    const baseDelay = retryInfo.retry_after_seconds || 1;

    switch (retryInfo.backoff_strategy) {
      case 'exponential':
        return baseDelay * Math.pow(2, attempt);
      case 'linear':
        return baseDelay * (attempt + 1);
      case 'fixed':
      default:
        return baseDelay;
    }
  }

  private showErrorToUser(message: string, type: 'error' | 'warning' | 'info'): void {
    // Implement your UI notification system
    console.log(`[${type.toUpperCase()}] ${message}`);
  }

  private logError(error: WebSocketError): void {
    // Send to your logging service
    console.error('WebSocket Error Details:', {
      error_code: error.error_code,
      correlation_id: error.correlation_id,
      timestamp: error.timestamp,
      details: error.details
    });
  }
}

// Usage
const socket = io();
const errorHandler = new WebSocketErrorHandler();

socket.on('oh_error', (error: WebSocketError) => {
  errorHandler.handleError(error);
});
```

### React Hook Example

```typescript
import { useEffect, useCallback } from 'react';
import { useToast } from '@/hooks/useToast';

export function useWebSocketErrorHandler(socket: any) {
  const { showToast } = useToast();

  const handleError = useCallback((error: WebSocketError) => {
    // Show user-friendly error message
    const userMessage = getUserFriendlyMessage(error);
    const toastType = getSeverityToastType(error.severity);

    showToast(userMessage, toastType);

    // Handle specific error types
    switch (error.error_code) {
      case 'WS_AUTH_1001':
      case 'WS_AUTH_1003':
        // Authentication errors - redirect to login
        window.location.href = '/login';
        break;

      case 'WS_CONN_1103':
        // Connection limit - show specific message
        showToast('Server is busy. Please try again in a few minutes.', 'warning');
        break;

      case 'WS_SYS_1403':
        // Rate limit - show countdown
        const retryAfter = error.retry_info?.retry_after_seconds || 60;
        showRateLimitMessage(retryAfter);
        break;
    }
  }, [showToast]);

  useEffect(() => {
    if (socket) {
      socket.on('oh_error', handleError);
      return () => socket.off('oh_error', handleError);
    }
  }, [socket, handleError]);
}

function getUserFriendlyMessage(error: WebSocketError): string {
  const friendlyMessages: Record<string, string> = {
    'WS_AUTH_1001': 'Authentication failed. Please log in again.',
    'WS_CONN_1102': 'Connection timed out. Please check your internet connection.',
    'WS_CONV_1301': 'Conversation not found. It may have been deleted.',
    'WS_SYS_1402': 'Service is temporarily unavailable. Please try again later.',
    'WS_SYS_1403': 'Too many requests. Please wait before trying again.',
  };

  return friendlyMessages[error.error_code] || error.message;
}
```

## Best Practices

### 1. Error Classification
- **Critical/High Severity**: Show immediate user notification, potentially disable features
- **Medium Severity**: Show notification, attempt automatic recovery
- **Low Severity**: Log for debugging, minimal user impact

### 2. Retry Logic
- Always check `retry_info.should_retry` before attempting retries
- Respect `retry_after_seconds` to avoid overwhelming the server
- Implement exponential backoff for connection errors
- Stop retrying after `max_retries` attempts

### 3. User Experience
- Show user-friendly error messages, not technical error codes
- Provide actionable guidance when possible
- Use the `help_url` field to link to relevant documentation
- Maintain application state during recoverable errors

### 4. Logging and Monitoring
- Log all errors with correlation IDs for debugging
- Track error patterns to identify systemic issues
- Monitor retry success rates
- Alert on critical error spikes

### 5. Security Considerations
- Don't expose sensitive information in error details to users
- Log security-related errors (authentication failures) for monitoring
- Implement rate limiting on client-side retry attempts

## Error Recovery Strategies

### Connection Errors
```typescript
// Implement connection recovery with backoff
class ConnectionManager {
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  async handleConnectionError(error: WebSocketError) {
    if (error.retry_info?.should_retry && this.reconnectAttempts < this.maxReconnectAttempts) {
      const delay = error.retry_info.retry_after_seconds || Math.pow(2, this.reconnectAttempts);

      setTimeout(() => {
        this.reconnectAttempts++;
        this.attemptReconnection();
      }, delay * 1000);
    } else {
      this.showConnectionFailedMessage();
    }
  }
}
```

### Authentication Errors
```typescript
// Handle authentication errors gracefully
function handleAuthError(error: WebSocketError) {
  // Clear invalid tokens
  localStorage.removeItem('auth_token');

  // Redirect to login with return URL
  const returnUrl = encodeURIComponent(window.location.pathname);
  window.location.href = `/login?return=${returnUrl}`;
}
```

### Rate Limiting
```typescript
// Handle rate limiting with user feedback
function handleRateLimit(error: WebSocketError) {
  const retryAfter = error.retry_info?.retry_after_seconds || 60;

  // Show countdown timer to user
  showRateLimitCountdown(retryAfter);

  // Disable submit buttons temporarily
  disableUserActions(retryAfter * 1000);
}
```

## Testing Error Handling

### Unit Tests
```typescript
describe('WebSocket Error Handler', () => {
  it('should retry connection errors with exponential backoff', () => {
    const error: WebSocketError = {
      error_code: 'WS_CONN_1102',
      message: 'Connection timeout',
      severity: 'medium',
      timestamp: Date.now(),
      retry_info: {
        should_retry: true,
        retry_after_seconds: 2,
        max_retries: 3,
        backoff_strategy: 'exponential'
      }
    };

    const handler = new WebSocketErrorHandler();
    handler.handleError(error);

    // Assert retry was scheduled
    expect(setTimeout).toHaveBeenCalledWith(expect.any(Function), 2000);
  });
});
```

### Integration Tests
```typescript
// Test error handling in real WebSocket scenarios
describe('WebSocket Integration', () => {
  it('should handle authentication errors correctly', async () => {
    const mockSocket = new MockWebSocket();
    const errorHandler = new WebSocketErrorHandler();

    mockSocket.emit('oh_error', {
      error_code: 'WS_AUTH_1001',
      message: 'Authentication failed',
      severity: 'high',
      timestamp: Date.now()
    });

    // Assert user was redirected to login
    expect(window.location.href).toBe('/login');
  });
});
```
