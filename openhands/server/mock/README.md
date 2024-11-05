# OpenHands Mock Server

A development server that simulates the OpenHands backend for frontend testing.

## Features

- WebSocket endpoint for real-time communication
- Simulated agent responses
- Basic error handling and validation
- Configurable timeouts and limits
- Debug logging for development

## Installation

Follow the instructions in the main README to install dependencies:

1. Install Python 3.12+
2. Install required packages:
   ```bash
   pip install fastapi uvicorn httpx
   ```

## Starting the Server

Run the development server:
```bash
python listen.py
```

The server will start on `http://127.0.0.1:3000` with WebSocket endpoint at `/ws`.

## Testing

1. Using `websocat`:
   ```bash
   websocat ws://127.0.0.1:3000/ws
   {"action": "start", "args": {"task": "test message"}}
   ```

2. Using `curl` for HTTP endpoints:
   ```bash
   curl http://127.0.0.1:3000/api/options/models
   curl http://127.0.0.1:3000/api/options/agents
   ```

## Error Handling

The server implements several error handling mechanisms:

1. WebSocket Errors:
   - Invalid JSON format
   - Connection timeouts
   - Protocol violations
   - State errors

2. HTTP Errors:
   - 400 Bad Request for invalid input
   - 404 Not Found for missing resources
   - 500 Internal Server Error for unexpected issues

3. Validation:
   - Message format checking
   - Size limits
   - Rate limiting
   - Protocol validation

## Debugging

The server provides detailed logging:

1. Start with debug logging:
   ```bash
   LOGLEVEL=debug python listen.py
   ```

2. Monitor WebSocket traffic:
   ```bash
   LOGLEVEL=debug python listen.py 2> websocket.log
   ```

## Limitations

This is a mock server intended for development only:
- No persistent storage
- Limited error handling
- No authentication
- No real agent execution

For production use, use the main OpenHands server.
