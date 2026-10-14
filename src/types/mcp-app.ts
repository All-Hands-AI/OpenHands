import type {
  CallToolRequest,
  CallToolResult,
  EmptyResult,
  ReadResourceResult,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import type {
  McpUiMessageRequest,
  McpUiMessageResult,
  McpUiUpdateModelContextRequest,
} from "@modelcontextprotocol/ext-apps";

/** Canvas presentation data, stored separately from canonical wire events. */
export interface MCPAppIntegrationData {
  tool: Pick<Tool, "name" | "_meta">;
  toolInput: Record<string, unknown>;
  toolResult: CallToolResult;
}

/** The embedding owns this sidecar and replaces the map when data changes. */
export type MCPAppArtifacts = ReadonlyMap<string, MCPAppIntegrationData>;

export interface MCPAppDescriptor extends MCPAppIntegrationData {
  resourceUri: string;
}

/** Trusted conversation identity, never supplied by the sandboxed application. */
export interface MCPAppScope {
  backendId: string;
  orgId: string | null;
  connectionRevision: number;
  conversationId: string;
  planningConversationId?: string | null;
  writableConversationId: string | null;
  readOnly?: boolean;
}

// @spec MCA-004 — MCP app sessions bind to the originating conversation and call
export interface MCPAppBinding {
  backendId: string;
  orgId: string | null;
  connectionRevision: number;
  ownerConversationId: string;
  eventId: string;
  actionId: string;
  toolCallId: string;
  toolName: string;
  resourceUri: string;
}

export interface MCPAppRequestOptions {
  signal: AbortSignal;
}

/** The adapter resolves the originating MCP server and keeps credentials private. */
export interface MCPAppSession {
  readResource(
    uri: string,
    options: MCPAppRequestOptions,
  ): Promise<ReadResourceResult>;
  callTool?(
    params: CallToolRequest["params"],
    options: MCPAppRequestOptions,
  ): Promise<CallToolResult>;
  updateModelContext?(
    params: McpUiUpdateModelContextRequest["params"],
    options: MCPAppRequestOptions,
  ): Promise<EmptyResult>;
  sendMessage?(
    params: McpUiMessageRequest["params"],
    options: MCPAppRequestOptions,
  ): Promise<McpUiMessageResult>;
  dispose?(): void | Promise<void>;
}

/** Optional frontend adapter; no built-in Agent Server endpoint is assumed. */
export interface MCPAppHost {
  sandboxUrl: string;
  open(
    binding: MCPAppBinding,
    options: MCPAppRequestOptions,
  ): Promise<MCPAppSession>;
}
