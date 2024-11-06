# 📦 EventStream Runtime

The OpenHands EventStream Runtime is the core component that enables secure and flexible execution of AI agent's action.
It creates a sandboxed environment using Docker, where arbitrary code can be run safely without risking the host system.

## Why do we need a sandboxed runtime?

OpenHands needs to execute arbitrary code in a secure, isolated environment for several reasons:

1. Security: Executing untrusted code can pose significant risks to the host system. A sandboxed environment prevents malicious code from accessing or modifying the host system's resources
2. Consistency: A sandboxed environment ensures that code execution is consistent across different machines and setups, eliminating "it works on my machine" issues
3. Resource Control: Sandboxing allows for better control over resource allocation and usage, preventing runaway processes from affecting the host system
4. Isolation: Different projects or users can work in isolated environments without interfering with each other or the host system
5. Reproducibility: Sandboxed environments make it easier to reproduce bugs and issues, as the execution environment is consistent and controllable

## How does the Runtime work?

The OpenHands Runtime system uses a client-server architecture implemented with Docker containers. Here's an overview of how it works:

```mermaid
graph TD
    A[User-provided Custom Docker Image] --> B[OpenHands Backend]
    B -->|Builds| C[OH Runtime Image]
    C -->|Launches| D[Action Executor]
    D -->|Initializes| E[Browser]
    D -->|Initializes| F[Bash Shell]
    D -->|Initializes| G[Plugins]
    G -->|Initializes| L[Jupyter Server]

    B -->|Spawn| H[Agent]
    B -->|Spawn| I[EventStream]
    I <--->|Execute Action to
    Get Observation
    via REST API
    | D

    H -->|Generate Action| I
    I -->|Obtain Observation| H

    subgraph "Docker Container"
    D
    E
    F
    G
    L
    end
```

1. User Input: The user provides a custom base Docker image
2. Image Building: OpenHands builds a new Docker image (the "OH runtime image") based on the user-provided image. This new image includes OpenHands-specific code, primarily the "runtime client"
3. Container Launch: When OpenHands starts, it launches a Docker container using the OH runtime image
4. Action Execution Server Initialization: The action execution server initializes an `ActionExecutor` inside the container, setting up necessary components like a bash shell and loading any specified plugins
5. Communication: The OpenHands backend (`openhands/runtime/impl/eventstream/eventstream_runtime.py`) communicates with the action execution server over RESTful API, sending actions and receiving observations
6. Action Execution: The runtime client receives actions from the backend, executes them in the sandboxed environment, and sends back observations
7. Observation Return: The action execution server sends execution results back to the OpenHands backend as observations


The role of the client:
- It acts as an intermediary between the OpenHands backend and the sandboxed environment
- It executes various types of actions (shell commands, file operations, Python code, etc.) safely within the container
- It manages the state of the sandboxed environment, including the current working directory and loaded plugins
- It formats and returns observations to the backend, ensuring a consistent interface for processing results


## How OpenHands builds and maintains OH Runtime images

OpenHands' approach to building and managing runtime images ensures efficiency, consistency, and flexibility in creating and maintaining Docker images for both production and development environments.

Check out the [relevant code](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/runtime/utils/runtime_build.py) if you are interested in more details.

### Image Tagging System

OpenHands uses a three-tag system for its runtime images to balance reproducibility with flexibility.
Tags may be in one of 2 formats:

- **Versioned Tag**: `oh_v{openhands_version}_{base_image}` (e.g.: `oh_v0.9.9_nikolaik_s_python-nodejs_t_python3.12-nodejs22`)
- **Lock Tag**: `oh_v{openhands_version}_{16_digit_lock_hash}` (e.g.: `oh_v0.9.9_1234567890abcdef`)
- **Source Tag**: `oh_v{openhands_version}_{16_digit_lock_hash}_{16_digit_source_hash}`
  (e.g.: `oh_v0.9.9_1234567890abcdef_1234567890abcdef`)


#### Source Tag - Most Specific

This is the first 16 digits of the MD5 of the directory hash for the source directory. This gives a hash
for only the openhands source


#### Lock Tag

This hash is built from the first 16 digits of the MD5 of:
- The name of the base image upon which the image was built (e.g.: `nikolaik/python-nodejs:python3.12-nodejs22`)
- The content of the `pyproject.toml` included in the image.
- The content of the `poetry.lock` included in the image.

This effectively gives a hash for the dependencies of Openhands independent of the source code.

#### Versioned Tag - Most Generic

This tag is a concatenation of openhands version and the base image name (transformed to fit in tag standard).

#### Build Process

When generating an image...

- **No re-build**: OpenHands first checks whether an image with the same **most specific source tag** exists. If there is such an image,
  no build is performed - the existing image is used.
- **Fastest re-build**: OpenHands next checks whether an image with the **generic lock tag** exists. If there is such an image,
  OpenHands builds a new image based upon it, bypassing all installation steps (like `poetry install` and
  `apt-get`) except a final operation to copy the current source code. The new image is tagged with a
  **source** tag only.
- **Ok-ish re-build**: If neither a **source** nor **lock** tag exists, an image will be built based upon the **versioned** tag image.
  In versioned tag image, most dependencies should already been installed hence saving time.
- **Slowest re-build**: If all of the three tags don't exists, a brand new image is built based upon the base
  image (Which is a slower operation). This new image is tagged with all the **source**, **lock**, and **versioned** tags.

This tagging approach allows OpenHands to efficiently manage both development and production environments.

1. Identical source code and Dockerfile always produce the same image (via hash-based tags)
2. The system can quickly rebuild images when minor changes occur (by leveraging recent compatible images)
3. The **lock** tag (e.g., `runtime:oh_v0.9.3_1234567890abcdef`) always points to the latest build for a particular base image, dependency, and OpenHands version combination

## Runtime Plugin System

The OpenHands Runtime supports a plugin system that allows for extending functionality and customizing the runtime environment. Plugins are initialized when the runtime client starts up.

Check [an example of Jupyter plugin here](https://github.com/All-Hands-AI/OpenHands/blob/ecf4aed28b0cf7c18d4d8ff554883ba182fc6bdd/openhands/runtime/plugins/jupyter/__init__.py#L21-L55) if you want to implement your own plugin.

*More details about the Plugin system are still under construction - contributions are welcomed!*

Key aspects of the plugin system:

1. Plugin Definition: Plugins are defined as Python classes that inherit from a base `Plugin` class
2. Plugin Registration: Available plugins are registered in an `ALL_PLUGINS` dictionary
3. Plugin Specification: Plugins are associated with `Agent.sandbox_plugins: list[PluginRequirement]`. Users can specify which plugins to load when initializing the runtime
4. Initialization: Plugins are initialized asynchronously when the runtime client starts
5. Usage: The runtime client can use initialized plugins to extend its capabilities (e.g., the JupyterPlugin for running IPython cells)
