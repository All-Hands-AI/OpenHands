import { io, Socket } from "socket.io-client";
import { OpenHandsParsedEvent } from "openhands-types";
import * as vscode from "vscode";
import * as path from "path";

export class SocketService {
  private socket: Socket | null = null;

  private serverUrl: string;

  private conversationId: string | null = null;

  private connectionId: string | null = null;

  private eventListeners: Array<(event: OpenHandsParsedEvent) => void> = [];

  private heartbeatInterval: NodeJS.Timeout | null = null;

  constructor(serverUrl: string) {
    this.serverUrl = serverUrl;
  }

  async connect(): Promise<void> {
    try {
      // Step 1: Register this VSCode instance with the server
      await this.registerVSCodeInstance();

      // Step 2: Initialize a conversation via HTTP API
      const response = await fetch(`${this.serverUrl}/api/conversations`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ initial_user_msg: "VSCode Runtime Connection" }),
      });

      if (!response.ok) {
        throw new Error(
          `Failed to initialize conversation: ${response.status} ${response.statusText}`,
        );
      }

      const data = await response.json();
      // TODO: Type check, do this better
      this.conversationId = (
        data as { conversation_id: string }
      ).conversation_id;

      // Now connect via Socket.IO
      this.socket = io(this.serverUrl, {
        query: {
          conversation_id: this.conversationId,
          latest_event_id: "-1",
        },
      });

      this.socket.on("connect", () => {
        console.log("Connected to OpenHands backend via Socket.IO");
      });

      this.socket.on("oh_event", (event: OpenHandsParsedEvent) => {
        console.log("Received event:", event);
        this.eventListeners.forEach((listener) => listener(event));
      });

      this.socket.on("disconnect", () => {
        console.log("Disconnected from OpenHands backend");
      });

      this.socket.on("error", (error: any) => {
        console.error("Socket.IO error:", error);
      });

      this.socket.on("connect_error", (error: any) => {
        console.error("Socket.IO connection error:", error);
      });

      // Step 3: Start heartbeat to keep registration alive
      this.startHeartbeat();
    } catch (error) {
      console.error("Error connecting to OpenHands backend:", error);
      throw error;
    }
  }

  disconnect(): void {
    // Stop heartbeat
    this.stopHeartbeat();

    // Unregister from VSCode registry
    if (this.connectionId) {
      this.unregisterVSCodeInstance().catch((error) => {
        console.error("Failed to unregister VSCode instance:", error);
      });
    }

    // Disconnect socket
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      console.log("Socket.IO connection closed");
    }

    // Reset state
    this.conversationId = null;
    this.connectionId = null;
  }

  onEvent(listener: (event: OpenHandsParsedEvent) => void): void {
    this.eventListeners.push(listener);
  }

  sendEvent(event: OpenHandsParsedEvent): void {
    if (this.socket && this.socket.connected) {
      this.socket.emit("oh_event", event);
      console.log("Sent event:", event);
    } else {
      console.error("Cannot send event: Socket is not connected");
    }
  }

  getConnectionId(): string | null {
    return this.connectionId;
  }

  private async registerVSCodeInstance(): Promise<void> {
    try {
      // Get workspace information
      const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
      const workspacePath = workspaceFolder?.uri.fsPath || "";
      const workspaceName =
        workspaceFolder?.name ||
        path.basename(workspacePath) ||
        "Unknown Workspace";

      // Get VSCode version
      const vscodeVersion = vscode.version;

      // Get extension version (from package.json)
      const extensionVersion =
        vscode.extensions.getExtension("openhands.openhands-vscode")
          ?.packageJSON?.version || "0.0.1";

      // Define capabilities
      const capabilities = [
        "file_operations",
        "text_editing",
        "workspace_navigation",
        "terminal_access",
      ];

      const registrationData = {
        workspace_path: workspacePath,
        workspace_name: workspaceName,
        vscode_version: vscodeVersion,
        extension_version: extensionVersion,
        capabilities,
      };

      console.log("Registering VSCode instance:", registrationData);

      const response = await fetch(`${this.serverUrl}/api/vscode/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(registrationData),
      });

      if (!response.ok) {
        throw new Error(
          `Failed to register VSCode instance: ${response.status} ${response.statusText}`,
        );
      }

      const data = await response.json();
      this.connectionId = (data as { connection_id: string }).connection_id;

      console.log(
        `VSCode instance registered with connection ID: ${this.connectionId}`,
      );
    } catch (error) {
      console.error("Error registering VSCode instance:", error);
      throw error;
    }
  }

  private async unregisterVSCodeInstance(): Promise<void> {
    if (!this.connectionId) {
      return;
    }

    try {
      const response = await fetch(
        `${this.serverUrl}/api/vscode/unregister/${this.connectionId}`,
        {
          method: "DELETE",
        },
      );

      if (!response.ok) {
        console.warn(
          `Failed to unregister VSCode instance: ${response.status} ${response.statusText}`,
        );
      } else {
        console.log(`VSCode instance unregistered: ${this.connectionId}`);
      }
    } catch (error) {
      console.error("Error unregistering VSCode instance:", error);
    }
  }

  private startHeartbeat(): void {
    if (!this.connectionId) {
      return;
    }

    // Send heartbeat every 30 seconds
    this.heartbeatInterval = setInterval(async () => {
      try {
        const response = await fetch(
          `${this.serverUrl}/api/vscode/heartbeat/${this.connectionId}`,
          {
            method: "POST",
          },
        );

        if (!response.ok) {
          console.warn(
            `Heartbeat failed: ${response.status} ${response.statusText}`,
          );
        }
      } catch (error) {
        console.error("Heartbeat error:", error);
      }
    }, 30000); // 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
}
