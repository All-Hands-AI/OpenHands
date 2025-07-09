# Runtime Pool

The Runtime Pool is a performance optimization feature that maintains a pool of pre-connected runtime instances to reduce the latency of runtime initialization.

## Overview

Runtime initialization can be slow, especially for containerized runtimes that need to start containers, install dependencies, and set up the environment. The Runtime Pool addresses this by:

1. Pre-creating and warming up runtime instances during application startup
2. Maintaining a pool of ready-to-use runtimes
3. Providing a proxy runtime that seamlessly uses pooled instances
4. Automatically managing pool size and runtime lifecycle

## Configuration

The Runtime Pool is configured using environment variables:

- `POOLED_RUNTIME_CLASS`: The runtime class to pool (e.g., 'local', 'docker', 'remote')
- `INITIAL_NUM_WARM_SERVERS`: Number of runtimes to create during startup (default: 1)
- `TARGET_NUM_WARM_SERVERS`: Target number of warm runtimes to maintain (default: 2)

If `POOLED_RUNTIME_CLASS` is not set, the pool is disabled and runtimes are created normally.

## Usage

### Basic Usage

```python
from openhands.runtime import get_runtime_cls

# Get the pooled runtime class
runtime_cls = get_runtime_cls('pooled')

# Create a pooled runtime instance
runtime = runtime_cls(config, event_stream)

# Connect (gets a runtime from the pool)
await runtime.connect()

# Use the runtime normally
result = runtime.run(action)

# Close (returns the runtime to the pool)
runtime.close()
```

### Environment Setup

```bash
export POOLED_RUNTIME_CLASS=local
export INITIAL_NUM_WARM_SERVERS=2
export TARGET_NUM_WARM_SERVERS=4
```

## Architecture

### RuntimePool Class

The `RuntimePool` is a singleton that manages the pool of runtime instances:

- **Setup**: Creates initial warm runtimes and starts maintenance thread
- **Get Runtime**: Provides a runtime from the pool or creates a new one
- **Return Runtime**: Resets and returns a runtime to the pool
- **Maintenance**: Background thread that maintains target pool size
- **Teardown**: Cleans up all runtimes and stops maintenance

### PooledRuntime Class

The `PooledRuntime` acts as a proxy for actual runtime instances:

- **Initialization**: Stores configuration but doesn't create actual runtime
- **Connect**: Gets a runtime from the pool and delegates to it
- **Method Delegation**: All runtime methods are forwarded to the actual runtime
- **Close**: Returns the runtime to the pool instead of destroying it

### Runtime Lifecycle

1. **Warm-up**: Runtimes are pre-created during pool setup
2. **Allocation**: When needed, a runtime is taken from the pool
3. **Usage**: The runtime is used normally through the proxy
4. **Reset**: When returned, the runtime is reset to a clean state
5. **Reuse**: The reset runtime is available for the next allocation

## Performance Benefits

- **Reduced Latency**: No runtime initialization delay for most requests
- **Better Resource Utilization**: Reuse of expensive runtime resources
- **Scalability**: Pool size can be tuned based on expected load
- **Graceful Degradation**: Falls back to normal runtime creation if pool is empty

## Implementation Details

### Thread Safety

The pool uses thread-safe data structures:
- `queue.Queue` for the runtime pool
- `threading.Lock` for critical sections
- `set` for tracking active runtimes (protected by locks)

### Runtime Reset

When a runtime is returned to the pool, it's reset to a clean state:
- Event stream is cleared
- Session ID is reset
- User context is cleared
- Status callbacks are removed

### Error Handling

- Failed runtime creation during warm-up is logged but doesn't stop the pool
- Runtime reset failures cause the runtime to be discarded
- Pool exhaustion falls back to creating new runtimes

### Memory Management

- Runtimes are properly cleaned up during teardown
- Failed runtimes are not returned to the pool
- Pool size is bounded to prevent memory leaks

## Monitoring and Debugging

The pool provides logging for key events:
- Pool setup and teardown
- Runtime creation and allocation
- Pool size changes
- Error conditions

Log messages include:
- `Runtime pooling enabled for {class}`
- `RuntimePool setup complete with {count} initial warm runtimes`
- `Failed to create warm runtime {i}: {error}`
- `Shutting down RuntimePool...`

## Limitations

- Only one runtime class can be pooled at a time
- Pool size is global, not per-session
- Runtime state must be properly resettable
- Additional memory overhead for maintaining warm runtimes

## Best Practices

1. **Tune Pool Size**: Set `INITIAL_NUM_WARM_SERVERS` and `TARGET_NUM_WARM_SERVERS` based on expected concurrent usage
2. **Monitor Performance**: Watch for pool exhaustion and adjust sizes accordingly
3. **Test Reset Logic**: Ensure runtime reset properly cleans up state
4. **Resource Limits**: Consider memory and CPU usage of warm runtimes
5. **Graceful Shutdown**: Always call teardown during application shutdown

## Example Configuration

For a high-traffic deployment:

```bash
export POOLED_RUNTIME_CLASS=docker
export INITIAL_NUM_WARM_SERVERS=5
export TARGET_NUM_WARM_SERVERS=10
```

For development:

```bash
export POOLED_RUNTIME_CLASS=local
export INITIAL_NUM_WARM_SERVERS=1
export TARGET_NUM_WARM_SERVERS=2
```

## Troubleshooting

### Pool Not Working

- Check that `POOLED_RUNTIME_CLASS` is set to a valid runtime class
- Verify the runtime class supports pooling (implements proper reset)
- Check logs for pool setup errors

### Performance Issues

- Monitor pool size vs. demand
- Increase `TARGET_NUM_WARM_SERVERS` if pool is frequently empty
- Check runtime reset performance

### Memory Usage

- Reduce pool size if memory usage is too high
- Monitor for runtime leaks during reset
- Ensure proper cleanup during teardown