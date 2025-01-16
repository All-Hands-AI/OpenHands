# OpenHands Glossary

### Agent
The core AI entity in OpenHands that can perform software development tasks by interacting with tools, browsing the web, and modifying code.

#### Agent Configuration
Settings that define an agent's behavior, capabilities, and limitations, including available tools and runtime settings.

#### Agent Controller
A component that manages the agent's lifecycle, handles its state, and coordinates interactions between the agent and various tools.

#### Agent Delegation
The ability of an agent to hand off specific tasks to other specialized agents for better task completion.

#### Agent Hub
A central registry of different agent types and their capabilities, allowing for easy agent selection and instantiation.

#### Agent Session
A persistent context that maintains the agent's state, history, and active tools during a conversation or task execution.

#### Agent Skill
A specific capability or function that an agent can perform, such as file manipulation, web browsing, or code editing.

#### Agent State
The current context and status of an agent, including its memory, active tools, and ongoing tasks.

#### CodeAct Agent
A specialized agent type in OpenHands designed specifically for software development tasks and code manipulation.

### Authentication
The system for verifying user identity and managing access to OpenHands features and services.

### Browser
A system for web-based interactions and tasks.

#### Browser Environment
A controlled web browser environment where agents can perform web-based tasks and interactions.

#### Browser Gym
A testing and evaluation environment for browser-based agent interactions and tasks.

#### Web Browser Tool
A tool that enables agents to interact with web pages and perform web-based tasks.

### Code
Software development and manipulation capabilities.

#### Code Analysis
The process of examining and understanding code structure, patterns, and potential issues.

#### Code Generation
The ability to create new code based on requirements, context, and existing codebase.

#### Code Modification
The process of making changes to existing code, including fixes, refactoring, and feature additions.

### Command
Terminal and execution related functionality.

#### Command Success
A mechanism for determining whether executed commands completed successfully and produced expected results.

#### Bash Parser
A component that processes and interprets bash commands and their outputs for agent interaction.

#### Bash Session
A persistent terminal session that maintains state and history for bash command execution.

### Configuration
System-wide settings and options.

#### Configuration Options
Settings that control various aspects of OpenHands behavior, including runtime, security, and agent settings.

#### LLM Config
Configuration settings for language models used by agents, including model selection and parameters.

#### LLM Draft Config
Settings for draft mode operations with language models, typically used for faster, lower-quality responses.

#### Security Options
Configuration settings that control security features and restrictions.

### Conversation
A sequence of interactions between a user and an agent, including messages, actions, and their results.

#### Conversation Info
Metadata about a conversation, including its status, participants, and timeline.

#### Conversation Manager
A component that handles the creation, storage, and retrieval of conversations.

#### Conversation Metadata
Additional information about conversations, such as tags, timestamps, and related resources.

#### Conversation Status
The current state of a conversation, including whether it's active, completed, or failed.

#### Conversation Store
A storage system for maintaining conversation history and related data.

### Event
A discrete occurrence in the system, such as an action being taken or an observation being made.

#### Action
A specific operation or command that an agent executes through available tools, such as running a command or editing a file.

##### Action Parser
A component that interprets and validates agent actions before they are executed in the runtime environment.

##### Action Serialization
The process of converting agent actions into a format that can be transmitted and executed in the runtime environment.

#### Event Serialization
The process of converting events into a format that can be stored and transmitted.

#### Event Stream
A continuous flow of events that represents the ongoing activities and interactions in the system.

#### Observation
The response or result returned by a tool after an agent's action, providing feedback about the action's outcome.

##### Observation Serialization
The process of converting tool observations into a format that can be stored and processed.

### File
File system operations and management.

#### File Editor
A tool that allows agents to view, create, and modify files in the runtime environment.

#### File Operations
Basic file system operations that agents can perform, such as reading, writing, and deleting files.

#### File Reader
A component that handles file reading operations with support for different file formats.

#### File Settings Store
A storage system for maintaining persistent settings and configurations.

### Interface
Different ways to interact with OpenHands.

#### CLI Mode
A command-line interface mode for interacting with OpenHands agents without a graphical interface.

#### GUI Mode
A graphical user interface mode for interacting with OpenHands agents through a web interface.

#### Headless Mode
A mode of operation where OpenHands runs without a user interface, suitable for automation and scripting.

#### VSCode Integration
Features that allow OpenHands to integrate with Visual Studio Code for development tasks.

### Issue Management
Tools and features for handling code issues and changes.

#### Issue Handler
A component that processes and manages GitHub issues and their resolution.

#### Issue References
Links and references to specific issues in version control systems or issue trackers.

#### Patch Apply
The process of applying code changes or patches to existing files.

### Memory
The system that maintains conversation history, context, and relevant information for the agent across interactions.

#### Memory Store
A storage system for maintaining agent memory and context across sessions.

#### Condenser
A component that processes and summarizes conversation history to maintain context while staying within token limits.

#### Chunk Localizer
A component that helps identify and locate specific chunks of text or code within larger files.

### Microagent
A specialized prompt that enhances OpenHands with domain-specific knowledge, repository-specific context, and task-specific workflows.

#### Microagent Registry
A central repository of available microagents and their configurations.

#### Public Microagent
A general-purpose microagent available to all OpenHands users, triggered by specific keywords.

#### Repository Microagent
A type of microagent that provides repository-specific context and guidelines, stored in the `.openhands/microagents/` directory.



### Prompt
Components for managing and processing prompts.

#### Prompt Caching
A system for caching and reusing common prompts to improve performance.

#### Prompt Manager
A component that handles the loading, processing, and management of prompts used by agents, including microagents.

#### Response Parsing
The process of interpreting and structuring responses from language models and tools.

### Runtime
The execution environment where agents perform their tasks, which can be local, remote, or containerized.

#### Action Execution Client
A component that handles the execution of actions in the runtime environment, managing the communication between the agent and the runtime.

#### Docker Runtime
A containerized runtime environment that provides isolation and reproducibility for agent operations.

#### E2B Runtime
A specialized runtime environment built on E2B for secure and isolated code execution.

#### Local Runtime
A runtime environment that executes on the local machine, suitable for development and testing.

#### Modal Runtime
A runtime environment built on Modal for scalable and distributed agent operations.

#### Remote Runtime
A sandboxed environment that executes code and commands remotely, providing isolation and security for agent operations.

#### Runtime Builder
A component that creates and configures runtime environments based on specifications.

#### Runtime Configuration
Settings that define how the runtime environment should be set up and operated.

#### Runtime Initialization
The process of setting up and preparing a runtime environment for agent use.

#### Runtime Reboot
The process of resetting and restarting a runtime environment when needed.

#### Sandbox
An isolated environment where agents can safely execute code and commands without affecting the host system.

#### Web Runtime
A specialized runtime environment that enables agents to interact with web browsers and perform web-based tasks.

### Security
Security-related components and features.

#### Security Analyzer
A component that checks agent actions for potential security risks.

### Settings
System settings and configuration storage.

#### Settings API
An interface for managing and accessing system and user settings.

#### Settings Store
A storage system for maintaining system and user settings.

### System
Core system components and features.

#### Async Completion
A mechanism for handling asynchronous LLM completions, allowing for non-blocking agent operations.

#### Function Calling
The mechanism by which agents invoke specific functions or tools to perform tasks.

#### Logging
The system for recording agent actions, errors, and system events for debugging and monitoring.

#### System Stats
Metrics and information about system performance and resource usage.

#### Task State
The current status and progress of a specific task being performed by an agent.

### Tool
A function or capability available to agents for performing specific tasks, like executing commands, editing files, or browsing the web.

#### Tool Registry
A central repository of available tools and their specifications.

#### Traffic Control
A system that manages and regulates the flow of requests and actions between agents and various services.

#### Truncation
The process of reducing conversation history or content to stay within token limits.
A component that handles the execution of actions in the runtime environment, managing the communication between the agent and the runtime.

### Action Parser
A component that interprets and validates agent actions before they are executed in the runtime environment.

### Action Serialization
The process of converting agent actions into a format that can be transmitted and executed in the runtime environment.

### Agent
The core AI entity in OpenHands that can perform software development tasks by interacting with tools, browsing the web, and modifying code.

### Agent Configuration
Settings that define an agent's behavior, capabilities, and limitations, including available tools and runtime settings.

### Agent Controller
A component that manages the agent's lifecycle, handles its state, and coordinates interactions between the agent and various tools.

### Agent Delegation
The ability of an agent to hand off specific tasks to other specialized agents for better task completion.

### Agent Hub
A central registry of different agent types and their capabilities, allowing for easy agent selection and instantiation.

### Agent Session
A persistent context that maintains the agent's state, history, and active tools during a conversation or task execution.

### Agent Skill
A specific capability or function that an agent can perform, such as file manipulation, web browsing, or code editing.

### Agent State
The current context and status of an agent, including its memory, active tools, and ongoing tasks.

### Async Completion
A mechanism for handling asynchronous LLM completions, allowing for non-blocking agent operations.

### Authentication
The system for verifying user identity and managing access to OpenHands features and services.

### Bash Parser
A component that processes and interprets bash commands and their outputs for agent interaction.

### Bash Session
A persistent terminal session that maintains state and history for bash command execution.

### Browser Environment
A controlled web browser environment where agents can perform web-based tasks and interactions.

### Browser Gym
A testing and evaluation environment for browser-based agent interactions and tasks.

### Chunk Localizer
A component that helps identify and locate specific chunks of text or code within larger files.

### CLI Mode
A command-line interface mode for interacting with OpenHands agents without a graphical interface.

### CodeAct Agent
A specialized agent type in OpenHands designed specifically for software development tasks and code manipulation.

### Code Analysis
The process of examining and understanding code structure, patterns, and potential issues.

### Code Generation
The ability to create new code based on requirements, context, and existing codebase.

### Code Modification
The process of making changes to existing code, including fixes, refactoring, and feature additions.

### Command Success
A mechanism for determining whether executed commands completed successfully and produced expected results.

### Condenser
A component that processes and summarizes conversation history to maintain context while staying within token limits.

### Configuration Options
Settings that control various aspects of OpenHands behavior, including runtime, security, and agent settings.

### Conversation
A sequence of interactions between a user and an agent, including messages, actions, and their results.

### Conversation Info
Metadata about a conversation, including its status, participants, and timeline.

### Conversation Manager
A component that handles the creation, storage, and retrieval of conversations.

### Conversation Metadata
Additional information about conversations, such as tags, timestamps, and related resources.

### Conversation Status
The current state of a conversation, including whether it's active, completed, or failed.

### Conversation Store
A storage system for maintaining conversation history and related data.

### Docker Runtime
A containerized runtime environment that provides isolation and reproducibility for agent operations.

### E2B Runtime
A specialized runtime environment built on E2B for secure and isolated code execution.

### Event
A discrete occurrence in the system, such as an action being taken or an observation being made.

### Event Serialization
The process of converting events into a format that can be stored and transmitted.

### Event Stream
A continuous flow of events that represents the ongoing activities and interactions in the system.

### File Editor
A tool that allows agents to view, create, and modify files in the runtime environment.

### File Operations
Basic file system operations that agents can perform, such as reading, writing, and deleting files.

### File Reader
A component that handles file reading operations with support for different file formats.

### File Settings Store
A storage system for maintaining persistent settings and configurations.

### Function Calling
The mechanism by which agents invoke specific functions or tools to perform tasks.

### GUI Mode
A graphical user interface mode for interacting with OpenHands agents through a web interface.

### Headless Mode
A mode of operation where OpenHands runs without a user interface, suitable for automation and scripting.

### Issue Handler
A component that processes and manages GitHub issues and their resolution.

### Issue References
Links and references to specific issues in version control systems or issue trackers.

### LLM Config
Configuration settings for language models used by agents, including model selection and parameters.

### LLM Draft Config
Settings for draft mode operations with language models, typically used for faster, lower-quality responses.

### Local Runtime
A runtime environment that executes on the local machine, suitable for development and testing.

### Logging
The system for recording agent actions, errors, and system events for debugging and monitoring.

### Memory
The system that maintains conversation history, context, and relevant information for the agent across interactions.

### Memory Store
A storage system for maintaining agent memory and context across sessions.

### Microagent
A specialized prompt that enhances OpenHands with domain-specific knowledge, repository-specific context, and task-specific workflows.

### Microagent Registry
A central repository of available microagents and their configurations.

### Modal Runtime
A runtime environment built on Modal for scalable and distributed agent operations.

### Observation
The response or result returned by a tool after an agent's action, providing feedback about the action's outcome.

### Observation Serialization
The process of converting tool observations into a format that can be stored and processed.

### Patch Apply
The process of applying code changes or patches to existing files.

### Prompt Caching
A system for caching and reusing common prompts to improve performance.

### Prompt Manager
A component that handles the loading, processing, and management of prompts used by agents, including microagents.

### Public Microagent
A general-purpose microagent available to all OpenHands users, triggered by specific keywords.

### Remote Runtime
A sandboxed environment that executes code and commands remotely, providing isolation and security for agent operations.

### Repository Microagent
A type of microagent that provides repository-specific context and guidelines, stored in the `.openhands/microagents/` directory.

### Response Parsing
The process of interpreting and structuring responses from language models and tools.

### Runtime
The execution environment where agents perform their tasks, which can be local, remote, or containerized.

### Runtime Builder
A component that creates and configures runtime environments based on specifications.

### Runtime Configuration
Settings that define how the runtime environment should be set up and operated.

### Runtime Initialization
The process of setting up and preparing a runtime environment for agent use.

### Runtime Reboot
The process of resetting and restarting a runtime environment when needed.

### Sandbox
An isolated environment where agents can safely execute code and commands without affecting the host system.

### Security Analyzer
A component that checks agent actions for potential security risks.

### Security Options
Configuration settings that control security features and restrictions.

### Session Manager
A component that handles the creation and management of agent sessions.

### Settings API
An interface for managing and accessing system and user settings.

### Settings Store
A storage system for maintaining system and user settings.

### System Stats
Metrics and information about system performance and resource usage.

### Task State
The current status and progress of a specific task being performed by an agent.

### Tool
A function or capability available to agents for performing specific tasks, like executing commands, editing files, or browsing the web.

### Tool Registry
A central repository of available tools and their specifications.

### Traffic Control
A system that manages and regulates the flow of requests and actions between agents and various services.

### Truncation
The process of reducing conversation history or content to stay within token limits.

### VSCode Integration
Features that allow OpenHands to integrate with Visual Studio Code for development tasks.

### Web Browser Tool
A tool that enables agents to interact with web pages and perform web-based tasks.

### Web Runtime
A specialized runtime environment that enables agents to interact with web browsers and perform web-based tasks.