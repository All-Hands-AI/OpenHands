# VsCodeRuntime: Leveraging VS Code as an OpenHands Execution Environment

## 1. Introduction and Concept

The `VsCodeRuntime` represents a paradigm where the OpenHands VS Code extension (`openhands-tab`) transcends its role as a mere UI and becomes an active execution environment for agent actions. Instead of the OpenHands backend relying solely on Python-based runtimes (like `CLIRuntime` for local execution or sandboxed environments like Docker/E2B) to perform tasks and then report results, the `VsCodeRuntime` model proposes that the backend delegates certain actions directly to the VS Code extension. The extension then utilizes native VS Code APIs to execute these actions (e.g., running commands in the integrated terminal, performing file operations using `vscode.workspace.fs`).

The primary goal is to achieve the deepest possible integration with the user's VS Code environment, providing a seamless and consistent experience where the agent operates directly within the tools and context the user sees and trusts.

*Reference: This document is based on discussions and analysis of the OpenHands codebase, including the principles of runtimes like `openhands/runtime/impl/cli/cli_runtime.py` and `openhands/runtime/impl/local/local_runtime.py`, the existing `openhands-tab` VS Code extension structure and plans (documented in `openhands/runtime/utils/vscode-extensions/openhands-tab/README.md` and `vscode_extension_status_and_plan.md`), and the event structures in `event_glossary.md`.*

## 2. Architecture Overview

The `VsCodeRuntime` system comprises two main parts, forming a client-server architecture for action execution:

*   **`VsCodeRuntime` (Python Backend Class):** A new Python class within the OpenHands backend that implements the `openhands.runtime.base.Runtime` interface. This class acts as the "server-side" component from the perspective of the agent controller. Its role is to receive `Action` objects from the agent controller and delegate them to the VS Code extension (the "client-side executor") via a Socket.IO connection, then await an `Observation` in response.
*   **VS Code Extension Execution Logic (Client-Side Executor):** TypeScript/JavaScript code within the `openhands-tab` extension. This part listens for action requests from the `VsCodeRuntime (Python Backend Class)`, executes these actions using native VS Code APIs, and sends back `Observation` objects.

The overall architecture involves the following key components:

*   **OpenHands Backend:** Contains the core agent logic, LLM interaction, and decision-making processes. This is where the `VsCodeRuntime (Python Backend Class)` resides and is invoked.
*   **`VsCodeRuntime` (Python Backend Class):** (As detailed above) This class receives `Action` objects (e.g., `CmdRunAction`, `FileReadAction`) from the agent controller, serializes them, and transmits them over an active Socket.IO connection to the connected VS Code extension, then awaits corresponding `Observation` objects.
*   **VS Code Extension (`openhands-tab`):** Acts as the direct execution environment (the "client-side executor") for actions delegated by the `VsCodeRuntime (Python Backend Class)`. It listens for these action requests on the Socket.IO channel, utilizes VS Code APIs to perform them, constructs `Observation` objects, and sends them back.
*   **Socket.IO Channel:** Serves as the bidirectional communication link between the `VsCodeRuntime (Python Backend Class)` on the backend and the `openhands-tab` VS Code extension.

## 2.5. Comparison with `LocalRuntime` and Pattern Leverage

The `VsCodeRuntime` system, particularly its backend Python component, shares conceptual similarities with the existing `LocalRuntime` (`openhands/runtime/impl/local/local_runtime.py`) but differs significantly in its execution mechanism and integration goals. Understanding these aspects is key for implementation.

### `LocalRuntime` Overview

*   **Purpose:** `LocalRuntime` runs a dedicated `action_execution_server` (a Python FastAPI application) directly on the local machine, without Docker.
*   **Mechanism:**
    1.  `LocalRuntime` (which inherits from `ActionExecutionClient`) sends `Action` objects via HTTP POST requests to this local `action_execution_server`.
    2.  The `action_execution_server` executes these actions using Python's `subprocess`, file I/O libraries, etc.
    3.  It returns an `Observation` in the HTTP response to `LocalRuntime`.

*(Reference: `openhands/runtime/impl/local/local_runtime.py` and `openhands/runtime/impl/action_execution/action_execution_client.py`)*

### Similarities with `VsCodeRuntime`

*   **Delegation Pattern:** Both involve the main OpenHands agent control loop delegating `Action` execution to another entity and receiving an `Observation` back.
*   **Client-Server Model (Conceptual):**
    *   `LocalRuntime` acts as a client to the `action_execution_server`.
    *   The `VsCodeRuntime (Python Backend Class)` will act as a client (in terms of initiating requests) to the VS Code extension's execution capabilities (which acts as a server for those specific requests).
*   **Local Execution Goal:** Both aim for execution on the user's local machine.

### Key Differences from `VsCodeRuntime`

| Feature                 | `LocalRuntime`                                                                 | `VsCodeRuntime` System                                     |
| :---------------------- | :----------------------------------------------------------------------------- | :------------------------------------------------------------------- |
| **Actual Executor**     | A separate Python process (`action_execution_server`).                         | The VS Code extension itself (TypeScript/JavaScript).                |
| **Execution Mechanism** | Python libraries (`subprocess`, `os`, etc.) within `action_execution_server`. | Native VS Code APIs (`vscode.Terminal`, `vscode.workspace.fs`).      |
| **Communication**       | HTTP POST (Python to Python).                                                  | Socket.IO (Python backend to VS Code extension).                     |
| **Integration Level**   | Separate local server; UI is decoupled.                                        | Deeply integrated with VS Code UI/UX.                                |

### Leveraging Patterns from `LocalRuntime` for `VsCodeRuntime (Python Backend Class)`

While the transport and executor are different, the `VsCodeRuntime (Python Backend Class)` can adapt several patterns from `LocalRuntime`'s interaction with its `action_execution_server`:

1.  **Implementing `openhands.runtime.base.Runtime`:** The new `VsCodeRuntime (Python Backend Class)` must implement the abstract methods of the `Runtime` base class (e.g., `async def run(self, action: CmdRunAction)`). This is analogous to how `ActionExecutionClient` (which `LocalRuntime` is a part of) fulfills this contract.
2.  **Action Serialization/Deserialization:**
    *   `LocalRuntime` (via `ActionExecutionClient`) serializes `Action` objects (implicitly by `httpx` for JSON payloads) to send to the `action_execution_server`. The server deserializes them.
    *   The `VsCodeRuntime (Python Backend Class)` will need to serialize `Action` objects (e.g., to JSON) to send over Socket.IO. The VS Code extension will deserialize them. The reverse is true for `Observation` objects.
    *   *(Reference: `openhands.events.serialization.event_to_dict` and `observation_from_dict` are used by `ActionExecutionClient` and could be relevant.)*
3.  **Request-Response Correlation:**
    *   While HTTP has a built-in request-response model, Socket.IO is event-based. The proposed `request_id` in `oh_runtime_action_request` and `oh_runtime_observation_response` events is crucial for the `VsCodeRuntime (Python Backend Class)` to correlate a sent action with its corresponding observation, especially with asynchronous operations. This ensures the correct `await` in the Python runtime resolves with the correct observation.
4.  **Error Handling:** The `VsCodeRuntime (Python Backend Class)` will need robust error handling for communication failures with the VS Code extension (e.g., timeouts if no `oh_runtime_observation_response` is received) and for errors reported by the extension within the `Observation` payload. This is similar to how `ActionExecutionClient` handles HTTP errors or errors from the `action_execution_server`.
5.  **Asynchronous Operations:** The methods in `VsCodeRuntime (Python Backend Class)` (like `async def run(...)`) will be asynchronous. They will `await` the response from the VS Code extension over Socket.IO.

By adapting these patterns, the implementation of the `VsCodeRuntime (Python Backend Class)` can be more straightforward, focusing on the specifics of Socket.IO communication and VS Code API interaction logic within the extension, rather than reinventing the core runtime interface or action/observation handling logic.

## 3. Communication Protocol (Socket.IO) using `oh_event` and `Event.id`/`Observation.cause`

### Reusing Existing Connection and Event Structure

The `VsCodeRuntime` functionality will leverage the existing Socket.IO connection that the `openhands-tab` extension establishes with the OpenHands backend for chat interactions. We will use the standard `oh_event` message structure for delegating actions to the VS Code extension and receiving observations back. Correlation between a delegated action and its resulting observation will be achieved using the `id` of the `oh_event` that carries the action, and the `cause` field of the `Observation` (which will be wrapped in a responding `oh_event`). This aligns with the OpenHands event-driven architecture and standard event properties.

*   *Reference: The current Socket.IO connection setup is initiated after an HTTP POST to `/api/conversations` to retrieve a `conversation_id`. The extension then connects to the WebSocket server (e.g., `ws://localhost:3000/`) with `conversation_id` and `latest_event_id` as query parameters. This process is outlined in `vscode_extension_status_and_plan.md` (Phase 2: Backend Communication) and its implementation is expected to reside in `src/extension/services/socket-service.ts` within the extension.*

### Action Delegation and Observation Flow using `Event.id` and `Observation.cause`

The communication for `VsCodeRuntime` will operate as follows:

1.  **Action Delegation (Backend to VS Code Extension):**
    *   The `VsCodeRuntime (Python Backend Class)` in the OpenHands backend decides to delegate an `Action` (e.g., `CmdRunAction`, `FileReadAction`) to the VS Code extension.
    *   It constructs the standard `Action` object (e.g., an instance of `CmdRunAction`).
    *   The backend then sends an `oh_event` over the existing Socket.IO connection. This `oh_event` will have its own unique `id` (e.g., `"delegated_action_event_123"`).
        *   The `action` field of this `oh_event` is the standard action type (e.g., `"run"` for `CmdRunAction`).
        *   The `args` field of this `oh_event` contains the arguments of the specific `Action`.
        *   The `VsCodeRuntime (Python Backend Class)` **must remember the `id` of this sent `oh_event`** (e.g., `"delegated_action_event_123"`) as it will expect an observation that cites this `id` as its `cause`.
    *   Optionally, for explicit routing by the extension, a marker like `execution_target: "vscode_runtime"` could be added to `oh_event.args` if needed, though the context of the `VsCodeRuntime` initiating this should be clear.

    *   **Example `oh_event` sent by backend for a delegated `CmdRunAction`:**
        ```json
        {
            "id": "delegated_action_event_123",       // Unique ID of this event, remembered by backend
            "action": "run",                          // Action type (e.g., CmdRunAction.action)
            "args": {                                 // Action arguments (CmdRunAction.args)
                "command": "ls -l",
                "thought": "Delegating command to VSCode for execution."
                // "execution_target": "vscode_runtime" // Optional marker for extension
                // ... other standard CmdRunAction args
            },
            "message": "Agent action delegated for VSCode execution.",
            "source": "agent",
            "timestamp": "YYYY-MM-DDTHH:mm:ss.sssZ"
        }
        ```

2.  **VS Code Extension Action Handling:**
    *   The VS Code extension's Socket.IO service listens for incoming `oh_event` messages.
    *   When an `oh_event` is received (e.g., the one with `id="delegated_action_event_123"`), the extension identifies it as a delegated action. This could be based on the `VsCodeRuntime` being active and the `oh_event` containing an `action` field (and potentially the optional `execution_target` marker in `oh_event.args`).
    *   The extension **notes the `id` of the received `oh_event`** (i.e., `"delegated_action_event_123"`).
    *   It then uses the `oh_event.action` type and `oh_event.args` to route the request to the appropriate internal handler for execution using VS Code APIs (as detailed in Section 4).

3.  **Observation Response (VS Code Extension to Backend):**
    *   After the VS Code extension executes the delegated action, it constructs the corresponding `Observation` object (e.g., `CmdOutputObservation`).
    *   **Crucially, the `cause` field of this `Observation` object is set to the `id` of the `oh_event` that initiated the action.** For example, `CmdOutputObservation.cause = "delegated_action_event_123"`.
    *   The extension then sends this `Observation` back to the backend, wrapped in a *new* standard `oh_event`.
        *   This new `oh_event` will have its own unique `id` (e.g., `"observation_response_event_456"`).
        *   The `observation` field of this `oh_event` is the standard observation type (e.g., `"run"` for `CmdOutputObservation`).
        *   The `content` and `extras` fields of this `oh_event` contain the details of the `Observation`.
        *   The `cause` field of this *outgoing `oh_event`* should also be set to `"delegated_action_event_123"` (the ID of the event that ultimately caused this observation response event).

    *   **Example `oh_event` sent by extension with the `CmdOutputObservation`:**
        ```json
        {
            "id": "observation_response_event_456",      // Unique ID of this response event
            "observation": "run",                        // Observation type
            "content": "total 0\ndrwxr-xr-x  2 user  staff    64 Jun  9 10:00 my_dir",
            "extras": {                                  // Observation extras
                "exit_code": 0,
                "command": "ls -l"
                // ... other standard CmdOutputObservation extras
            },
            "message": "VSCode executed delegated command and is reporting observation.",
            "source": "agent", // Or a more specific source like "vscode_runtime_executor"
            "cause": "delegated_action_event_123",       // ID of the oh_event that contained the Action
            "timestamp": "YYYY-MM-DDTHH:mm:ss.sssZ"
        }
        ```
        *(Note: In the Python `BaseObservation` class, the `cause` field is `_cause`. The `cause` property accesses this. The JSON serialization should reflect the property name `cause`.)*

4.  **Backend Correlation and Processing:**
    *   The `VsCodeRuntime (Python Backend Class)` on the backend listens for incoming `oh_event` messages.
    *   When it receives an `oh_event` that contains an `Observation` (i.e., `oh_event.observation` is set), it inspects the `cause` field of the *`Observation` object itself* (which is accessible via `oh_event.cause` if the `oh_event` directly wraps the observation's fields, or more precisely, from the deserialized `Observation` object's `cause` property).
    *   **If this `cause` value (e.g., `"delegated_action_event_123"`) matches an `id` of an `oh_event` it previously sent for delegation and is awaiting a response for, it uses this `Observation`** (primarily from `oh_event.content` and `oh_event.extras`) to resolve the pending asynchronous operation (e.g., the `await` in its `async def run(...)` method).

### Relationship with Existing Chat Events

This mechanism operates on the same `oh_event` channel used for regular agent-UI chat interactions:

*   `oh_user_action`: Still used by the extension to send user messages/prompts to the backend. This is an `Action` (typically `UserMessageAction`) sent from the UI, wrapped in an `oh_event`.
*   `oh_event` (from backend, for UI display): The backend will continue to send `oh_event` messages containing `Action`s (like `AgentThinkAction`, `AgentMessageAction`) or `Observation`s (from *other* runtimes or general agent state changes) intended for display in the VS Code extension's chat UI. These will typically have their own `cause` lineage but are not part of this specific `VsCodeRuntime` request-response flow.

The VS Code extension will need to differentiate:
    a. Incoming `oh_event`s where `oh_event.action` is set (and potentially `oh_event.args.execution_target == "vscode_runtime"` if that marker is used). These are for `VsCodeRuntime` execution. The extension must note the `id` of this event to later set as the `cause` of the resulting `Observation`.
    b. Other `oh_event`s (e.g., where `oh_event.observation` is set, or `oh_event.action` is set but is for UI display like an agent thought) which are for display in the chat UI as usual.

This refined approach leverages standard event properties (`Event.id` and `Observation.cause`) for correlation, ensuring consistency with the OpenHands event model and simplifying the protocol.

## 4. Action Execution in VS Code Extension

The general workflow within the VS Code extension for handling delegated actions (i.e., actions sent from the `VsCodeRuntime (Python Backend Class)`) would be:

1.  The extension's Socket.IO service (e.g., `src/extension/services/socket-service.ts`) listens for incoming `oh_event` messages from the backend.
2.  When an `oh_event` is received, the extension identifies it as a delegated action. This is typically done by checking if `oh_event.action` is set and potentially if `oh_event.args.execution_target === "vscode_runtime"` (if this optional marker is used, as described in Section 3).
3.  The extension **must record the `id` of this incoming `oh_event`** (e.g., `"delegated_action_event_123"`). This ID will be used as the `cause` for the resulting `Observation`.
4.  The request is routed to a dedicated handler module/service within the extension based on the `oh_event.action` type (e.g., "run", "read", "write"). The handler receives the `oh_event.args` (which contains the action-specific parameters).
5.  This handler uses the appropriate `vscode` APIs to execute the action.
6.  An `Observation` object is constructed based on the outcome of the execution. **Crucially, the `cause` field of this `Observation` object is set to the `id` recorded in step 3** (e.g., `Observation.cause = "delegated_action_event_123"`).
7.  The extension then sends this `Observation` back to the backend, wrapped in a new `oh_event`.
    *   This new outgoing `oh_event` will have its own unique `id`.
    *   The `observation` field of this outgoing `oh_event` is set to the type of the observation (e.g., "run", "read").
    *   The `content` and `extras` fields of this `oh_event` are populated from the constructed `Observation` object.
    *   The `cause` field of this outgoing `oh_event` is also set to the `id` of the original delegated action event (e.g., `"delegated_action_event_123"`).
    *   The `cause` field of this `oh_event` is set to the `id` of the incoming `oh_event` that contained the delegated action.

### `CmdRunAction` Handling

*   **APIs:**
    *   `vscode.window.createTerminal(options?: TerminalOptions)`: To create or get a reference to an integrated terminal (e.g., one named "OpenHands Agent").
    *   `vscode.Terminal.sendText(text: string, addNewLine?: boolean)`: To execute the command.
    *   `vscode.Terminal.show(preserveFocus?: boolean)`: To make the terminal visible.
*   **Workspace Context:** Commands would typically execute in the context of the current VS Code workspace root (`vscode.workspace.workspaceFolders[0].uri.fsPath`).
*   **Output Capturing & Challenges:**
    *   `vscode.window.onDidWriteTerminalData((e: { terminal: vscode.Terminal, data: string }) => {})` can be used to capture terminal output. The extension would need to filter data for the specific terminal instance it's using for the agent.
    *   **Challenges:** Reliably determining command completion and capturing the correct exit code is non-trivial with `sendText`.
        *   *Potential Solutions:* Suffixing commands with unique markers (e.g., `command_to_run; echo "COMMAND_COMPLETE_MARKER:$?"`) and parsing this marker from the output. The `vscode.Pseudoterminal` API offers more fine-grained control but is significantly more complex to implement.
*   **Observation:** A `CmdOutputObservation` is constructed with the captured stdout/stderr and the best-effort exit code.

### `FileReadAction` Handling

*   **API:** `vscode.workspace.fs.readFile(uri: vscode.Uri)`
*   **Path:** The `path` from `FileReadAction.args` would be resolved relative to the VS Code workspace root or handled as an absolute path. `vscode.Uri.file(path)` creates the URI.
*   **Observation:** A `FileReadObservation` containing the file content (as a string) or an error if the read fails.

### `FileWriteAction` Handling

*   **API:** `vscode.workspace.fs.writeFile(uri: vscode.Uri, content: Uint8Array)`
*   **Content:** The `content` from `FileWriteAction.args` would be converted to a `Uint8Array` (e.g., `Buffer.from(content)`).
*   **Observation:** A `FileWriteObservation` confirming success or detailing an error.

### `FileEditAction` Handling

This action is more complex as it can involve operations beyond simple overwrites (e.g., search-and-replace, insertions). The current `FileEditAction` in OpenHands is designed to work with an `OHEditor` backend.
*Reference: `openhands_aci.editor.editor.OHEditor` and its usage in `CLIRuntime`.*

*   **Option 1 (Full Content Replacement):** If the `FileEditAction` can be adapted or is used such that `args.content` contains the *entire new file content*, then `vscode.workspace.fs.writeFile` can be used, similar to `FileWriteAction`.
*   **Option 2 (Applying Diff/Specific Edits):** For more granular edits:
    *   **API:** `vscode.workspace.applyEdit(edit: vscode.WorkspaceEdit)`
    *   The extension would need to translate the `FileEditAction` arguments (e.g., `old_str`, `new_str`, `insert_line`, or a diff format if provided) into `vscode.TextEdit` objects. A `vscode.WorkspaceEdit` can then apply these text edits.
    *   This approach integrates seamlessly with VS Code's undo/redo stack and change tracking.
    *   This might require the backend to send more structured edit information (like diffs) or for the extension to incorporate logic similar to `OHEditor` to calculate the necessary `TextEdit` objects.
*   **Observation:** A `FileEditObservation`, potentially including a diff of the changes or a confirmation message.

## 5. Backend: `VsCodeRuntime` (Python Backend Class)

*   **Purpose:** This new Python class on the backend would implement the `Runtime` abstract base class (defined in `openhands.runtime.base`). It serves as the crucial bridge, forwarding actions meant for VS Code execution.
*   **Key Methods to Override (Examples):**
    *   `async def run(self, action: CmdRunAction) -> Observation:`: Serializes `action`, sends it via `oh_runtime_action_request`, and awaits an `oh_runtime_observation_response` to return the `CmdOutputObservation`.
    *   `async def read(self, action: FileReadAction) -> Observation:`: Similar flow for file reads.
    *   `async def write(self, action: FileWriteAction) -> Observation:`: Similar flow for file writes.
    *   `async def edit(self, action: FileEditAction) -> Observation:`: Similar flow for file edits.
    *   Other actions like `IPythonRunCellAction` could also be routed if a corresponding VS Code integration (e.g., with Jupyter extension APIs) is developed.
*   **State Management:** Primarily involves managing the request-response lifecycle using the `request_id` to correlate outgoing actions with incoming observations. It would also handle timeouts if the extension doesn't respond.

## 6. Initialization and Connection Flow

1.  The user opens the OpenHands tab in their VS Code instance.
2.  The `openhands-tab` extension initiates a conversation with the OpenHands backend. This typically involves an HTTP POST to `/api/conversations` to obtain a `conversation_id`. (*Reference: `src/extension/services/conversation-service.ts` and `vscode_extension_status_and_plan.md`*).
3.  The extension establishes a Socket.IO connection to the backend using the `conversation_id`. (*Reference: `src/extension/services/socket-service.ts`*).
4.  **Runtime Selection:** The OpenHands backend needs to be configured or decide (e.g., based on agent capabilities or session parameters) to use the `VsCodeRuntime (Python Backend Class)` for this specific agent session. This selection mechanism is a key design consideration for the backend.
5.  Once the `VsCodeRuntime (Python Backend Class)` is active for the session on the backend and the Socket.IO connection is established and ready:
    *   The backend can begin sending `oh_runtime_action_request` events to the extension for actions that should be executed within VS Code.
    *   The extension listens for these requests, processes them using `vscode` APIs, and sends back `oh_runtime_observation_response` events.
    *   Standard chat messages and other agent events (thoughts, observations from other runtimes if any are mixed) continue to flow over the same Socket.IO connection using existing event names like `oh_event`.

## 7. Benefits

*   **Deep Native Integration:** Actions are performed using VS Code's own terminals, editors, and file system APIs, providing a familiar and powerful user experience.
*   **Consistent Environment:** The agent operates on the exact file system and terminal environment that the user is currently working with.
*   **Leverages VS Code UI/UX:** Utilizes VS Code's built-in features for displaying command output, file content, diffs, etc.
*   **Simplified Agent Actions (Potentially):** The agent can express intent (e.g., "edit file X to achieve Y") and the VS Code extension, with its understanding of the local environment, can handle the specifics.

## 8. Challenges and Considerations

*   **Command Execution Robustness:** Reliably capturing command completion status, exit codes, and handling interactive prompts within commands sent via `vscode.Terminal.sendText()` is complex.
*   **Security:** Actions are executed with the user's permissions directly on their machine. Clear user consent, visibility of actions, and leveraging VS Code's workspace trust model are paramount.
*   **Error Handling and Propagation:** Ensuring robust error reporting and handling across the extension, the Socket.IO channel, and the backend runtime.
*   **`FileEditAction` Complexity:** Translating the intent of `FileEditAction` (which might be based on `OHEditor` logic) into precise `vscode.TextEdit` operations may require careful design.
*   **Backend Configuration:** Defining how and when the `VsCodeRuntime (Python Backend Class)` is selected and activated for an agent session.
*   **Resource Management:** The extension needs to manage resources it creates, such as terminal instances.
*   **Asynchronous Nature:** Both VS Code APIs and Socket.IO are heavily asynchronous, requiring careful management of promises and callbacks.

## 9. Future Possibilities

*   **Interactive Command Input:** Enabling the agent to prompt the user for input within a VS Code terminal it controls.
*   **Debugger Integration:** Allowing the agent to interact with VS Code's debugging capabilities.
*   **Testing UI Integration:** Agent actions could trigger or interact with VS Code's testing UIs.
*   **Enhanced `IPythonRunCellAction`:** Deeper integration with VS Code's Jupyter extension APIs for richer Python execution.
