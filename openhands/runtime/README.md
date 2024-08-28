# OpenHands Runtime

## Introduction

The OpenHands Runtime folder contains the core components responsible for executing actions and managing the runtime environment for the OpenHands project. This README provides an overview of the main components and their interactions.
You can learn more about how the runtime works in the [EventStream Runtime](https://docs.all-hands.dev/modules/usage/architecture/runtime) documentation.

## Main Components

### 1. runtime.py

The `runtime.py` file defines the `Runtime` class, which serves as the primary interface for agent interactions with the external environment. It handles various operations including:

- Bash sandbox execution
- Browser interactions
- Filesystem operations
- Environment variable management
- Plugin management

Key features of the `Runtime` class:
- Initialization with configuration and event stream
- Asynchronous initialization (`ainit`) for setting up environment variables
- Action execution methods for different types of actions (run, read, write, browse, etc.)
- Abstract methods for file operations (to be implemented by subclasses)

### 2. client/client.py

The `client.py` file contains the `RuntimeClient` class, which is responsible for executing actions received from the OpenHands backend and producing observations. This client runs inside a Docker sandbox.

Key features of the `RuntimeClient` class:
- Initialization of user environment and bash shell
- Plugin management and initialization
- Execution of various action types (bash commands, IPython cells, file operations, browsing)
- Integration with BrowserEnv for web interactions

## Workflow Description

1. **Initialization**:
   - The `Runtime` is initialized with configuration and event stream.
   - Environment variables are set up using `ainit` method.
   - Plugins are loaded and initialized.

2. **Action Handling**:
   - The `Runtime` receives actions through the event stream.
   - Actions are validated and routed to appropriate execution methods.

3. **Action Execution**:
   - Different types of actions are executed:
     - Bash commands using `run` method
     - IPython cells using `run_ipython` method
     - File operations (read/write) using `read` and `write` methods
     - Web browsing using `browse` and `browse_interactive` methods

4. **Observation Generation**:
   - After action execution, corresponding observations are generated.
   - Observations are added to the event stream.

5. **Plugin Integration**:
   - Plugins like Jupyter and AgentSkills are initialized and integrated into the runtime.

6. **Sandbox Environment**:
   - The `RuntimeClient` sets up a sandboxed environment inside a Docker container.
   - User environment and bash shell are initialized.
   - Actions received from the OpenHands backend are executed in this sandboxed environment.

7. **Browser Interactions**:
   - Web browsing actions are handled using the `BrowserEnv` class.

## Important Notes

- The runtime uses asynchronous programming (asyncio) for efficient execution.
- Environment variables can be added dynamically to both IPython and Bash environments.
- File operations and command executions are abstracted, allowing for different implementations in subclasses.
- The system uses a plugin architecture for extensibility.
- All interactions with the external environment are managed through the Runtime, ensuring a controlled and secure execution environment.

## Related Components

- The runtime interacts closely with the event system defined in the `openhands.events` module.
- It relies on configuration classes from `openhands.core.config`.
- Logging is handled through `openhands.core.logger`.

This section provides an overview of the OpenHands Runtime folder. For more detailed information on specific components or usage, please refer to the individual files and their docstrings.
