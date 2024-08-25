# OpenHands Runtime

## Introduction

The OpenHands Runtime folder contains the core components responsible for executing actions and managing the runtime environment for the OpenHands project. This README provides an overview of the main components and their interactions.

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

## Server Components

The following section describes the server-side components of the OpenHands project.

### 1. session/session.py

The `session.py` file defines the `Session` class, which represents a WebSocket session with a client. Key features include:

- Handling WebSocket connections and disconnections
- Initializing and managing the agent session
- Dispatching events between the client and the agent
- Sending messages and errors to the client

### 2. session/agent.py

The `agent.py` file contains the `AgentSession` class, which manages the lifecycle of an agent within a session. Key features include:

- Creating and managing the runtime environment
- Initializing the agent controller
- Handling security analysis
- Managing the event stream

### 3. session/manager.py

The `manager.py` file defines the `SessionManager` class, which is responsible for managing multiple client sessions. Key features include:

- Adding and restarting sessions
- Sending messages to specific sessions
- Cleaning up inactive sessions

### 4. listen.py

The `listen.py` file is the main server file that sets up the FastAPI application and defines various API endpoints. Key features include:

- Setting up CORS middleware
- Handling WebSocket connections
- Managing file uploads
- Providing API endpoints for agent interactions, file operations, and security analysis
- Serving static files for the frontend

## Workflow Description

1. **Server Initialization**:
   - The FastAPI application is created and configured in `listen.py`.
   - CORS middleware and static file serving are set up.
   - The `SessionManager` is initialized.

2. **Client Connection**:
   - When a client connects via WebSocket, a new `Session` is created or an existing one is restarted.
   - The `Session` initializes an `AgentSession`, which sets up the runtime environment and agent controller.

3. **Agent Initialization**:
   - The client sends an initialization request.
   - The server creates and configures the agent based on the provided parameters.
   - The runtime environment is set up, and the agent controller is initialized.

4. **Event Handling**:
   - The `Session` manages the event stream between the client and the agent.
   - Events from the client are dispatched to the agent.
   - Observations from the agent are sent back to the client.

5. **File Operations**:
   - The server handles file uploads, ensuring they meet size and type restrictions.
   - File read and write operations are performed through the runtime environment.

6. **Security Analysis**:
   - If configured, a security analyzer is initialized for each session.
   - Security-related API requests are forwarded to the security analyzer.

7. **Session Management**:
   - The `SessionManager` periodically cleans up inactive sessions.
   - It also handles sending messages to specific sessions when needed.

8. **API Endpoints**:
   - Various API endpoints are provided for agent interactions, file operations, and retrieving configuration defaults.

This server architecture allows for managing multiple client sessions, each with its own agent instance, runtime environment, and security analyzer. The event-driven design facilitates real-time communication between clients and agents, while the modular structure allows for easy extension and maintenance of different components.
