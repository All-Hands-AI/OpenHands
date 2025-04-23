# Port Overflow Fix

## Issue Description

The Action Execution Server was experiencing an `OverflowError` when trying to bind to a port outside the valid range (0-65535). This occurred when the server was started with a high port number, and the code attempted to calculate a range for the file viewer server by adding 10000 to the base port.

Error message:
```
ERROR:root:<class 'OverflowError'>: bind(): port must be 0-65535.
```

## Fix Implementation

The fix has been implemented in two places:

1. In `action_execution_server.py`, we ensure the maximum port number doesn't exceed 65535:
   ```python
   _file_viewer_port = find_available_tcp_port(
       min_port=args.port + 1, max_port=min(65535, args.port + 10000)
   )
   ```

2. In `system.py`, we added validation to the `find_available_tcp_port` function to ensure both min_port and max_port are within the valid range (0-65535):
   ```python
   # Ensure ports are within valid range (0-65535)
   min_port = max(0, min(min_port, 65535))
   max_port = max(min_port, min(max_port, 65535))
   ```

## Testing

The fix was tested with a simple script that verifies the function works correctly with both normal and potentially invalid port ranges:

```python
# Test with normal range
port1 = find_available_tcp_port(min_port=30000, max_port=39999)
print(f"Normal range port: {port1}")

# Test with potentially invalid range
port2 = find_available_tcp_port(min_port=65000, max_port=75000)
print(f"Potentially invalid range port: {port2}")

# Test with args.port + 10000 pattern
args_port = 60000
port3 = find_available_tcp_port(min_port=args_port + 1, max_port=min(65535, args_port + 10000))
print(f"With args.port pattern: {port3}")
```

All tests passed, confirming that the function now properly handles port ranges that might exceed the valid range.