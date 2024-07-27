# OpenDevin Runtime

This README provides an overview of the OpenDevin Runtime, a crucial component of the OpenDevin system. It covers two main aspects:

1. How the Runtime Image is Built: Explains the layered approach to creating Docker images for both production and development environments.
2. How the Runtime Client Works: Details the functionality and architecture of the Runtime Client, which executes actions within the Docker sandbox.

The following sections dive deeper into these topics, providing a comprehensive understanding of the OpenDevin Runtime system.

## Architecture Diagram

```
+-------------------+     +-------------------+
|   OpenDevin       |     |   Docker Host     |
|   Backend         |     |                   |
|                   |     |  +-------------+  |
|  +-------------+  |     |  |  Runtime    |  |
|  | EventStream |  |     |  |  Container  |  |
|  | Runtime     |<-|-----|->|             |  |
|  +-------------+  |     |  |  +-------+  |  |
|                   |     |  |  |Runtime|  |  |
|                   |     |  |  |Client |  |  |
|                   |     |  |  +-------+  |  |
|                   |     |  |     |       |  |
|                   |     |  |  +-------+  |  |
|                   |     |  |  |Plugins|  |  |
|                   |     |  |  +-------+  |  |
|                   |     |  +-------------+  |
+-------------------+     +-------------------+
```

This diagram illustrates the high-level architecture of the OpenDevin Runtime system:

1. The OpenDevin Backend communicates with the Docker Host through the EventStreamRuntime.
2. The Docker Host runs a Runtime Container, which includes:
   - The Runtime Client: Handles incoming actions and generates observations.
   - Plugins: Extend the functionality of the Runtime Client.
3. The Runtime Client executes actions within the sandboxed environment of the Docker container.

This architecture ensures a secure and flexible environment for executing AI-driven development tasks, allowing OpenDevin to execute a wide range of actions safely and efficiently.

## How the Runtime Image is Built

The OpenDevin runtime uses a layered approach for building Docker images:

1. **Original Image**: `ubuntu:22.04`
   - This is the base image used for all subsequent layers.

2. **Runtime Image**:  `od_runtime:od_v{OPENDEVIN_VERSION}_image_ubuntu__22.04`

Example image name: `od_runtime:od_v0.8.1_image_ubuntu__22.04`
   - Built from the stable release of OpenDevin.
   - This is the primary runtime image that users will interact with.
   - Created by copying all OpenDevin code into the original image and installing dependencies using Poetry.

1. **Dev Runtime Image**:  `od_runtime_dev:od_v{OPENDEVIN_VERSION}_image_ubuntu__22.04`
   - Built from local source code for development purposes.

### Build Process

#### Production Build (if environment variable `SANDBOX_UPDATE_SOURCE_CODE` is not set)
By default, when `SANDBOX_UPDATE_SOURCE_CODE` is unset OR set to false, the build process only needs to run once:
- The Runtime Image (`od_runtime:od_v{OPENDEVIN_VERSION}_image_ubuntu__22.04`) is created by copying OpenDevin code into the original Ubuntu image and installing all dependencies.
- This pre-built image is then used for running the OpenDevin environment.

#### Development Build (env var `SANDBOX_UPDATE_SOURCE_CODE=True`)
When developing or modifying code that runs inside the container, you can set env var `SANDBOX_UPDATE_SOURCE_CODE=True` to enable a more dynamic build process:
- Every time you run the code, the existing image will be updated with the latest changes.
- The Dev Runtime Image (`od_runtime_dev:od_v{OPENDEVIN_VERSION}_image_ubuntu__22.04`) is rebuilt from the Runtime Image (`od_runtime:od_v{OPENDEVIN_VERSION}_image_ubuntu__22.04`).
- Most dependencies are already installed in the Runtime Image, so this process mainly updates the code and any new dependencies.
- The rebuild process typically takes around 10 seconds, allowing for quick iterations during development.

This approach allows developers to easily test changes to the OpenDevin codebase, including modifications to files like client.py, without needing to rebuild the entire image from scratch each time.

## How the Runtime Client Works

The Runtime Client is a crucial component of the OpenDevin system, responsible for executing actions within the Docker sandbox environment and producing observations. Here's an overview of its functionality:

1. **Initialization**:
   - The `EventStreamRuntime` class in `runtime.py` initializes the Docker container and sets up the runtime environment.

2. **Communication**:
   - The Runtime Client uses FastAPI to create a web server inside the Docker container.
   - It listens for incoming action requests from the OpenDevin backend.

3. **Action Execution**:
   - When an action is received, the Runtime Client processes it based on its type:
     - `CmdRunAction`: Executes shell commands using a pexpect-spawned bash shell.
     - `FileReadAction` and `FileWriteAction`: Perform file operations within the sandbox.
     - `IPythonRunCellAction`: Executes Python code in an IPython environment.
     - `BrowseURLAction` and `BrowseInteractiveAction`: Handle web browsing tasks using a browser environment.

4. **Plugin System**:
   - The Runtime Client supports a plugin system for extending functionality.
   - Plugins like JupyterPlugin can be loaded to provide additional features.

5. **Observation Generation**:
   - After executing an action, the Runtime Client generates an appropriate observation.
   - Observations include command outputs, file contents, error messages, etc.

6. **Asynchronous Operation**:
   - The Runtime Client uses asyncio for avoid concurrent requests.
   - It ensures that only one action is executed at a time using a semaphore.

7. **Security**:
   - All actions are executed within the confined Docker environment, providing a sandbox for safe execution.

8. **Flexibility**:
   - The system supports both production (`SANDBOX_UPDATE_SOURCE_CODE=False`) and development (`SANDBOX_UPDATE_SOURCE_CODE=True`) modes.
   - In development mode, the runtime image can be updated with the latest code changes for testing and debugging.
