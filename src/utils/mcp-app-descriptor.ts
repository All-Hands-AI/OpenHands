import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import type { OpenHandsEvent } from "#/types/agent-server/core";
import type { MCPAppDescriptor } from "#/types/mcp-app";

const LEGACY_RESOURCE_URI_META_KEY = "ui/resourceUri";
const UI_RESOURCE_URI_PATTERN = /^ui:\/\/[^\s]+$/;

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function getResourceUri(meta: Record<string, unknown>): string | null {
  // A nested declaration takes precedence even when malformed. Falling back
  // would silently load a different app than the server's current declaration.
  const candidate = Object.prototype.hasOwnProperty.call(meta, "ui")
    ? isRecord(meta.ui)
      ? meta.ui.resourceUri
      : undefined
    : meta[LEGACY_RESOURCE_URI_META_KEY];
  return typeof candidate === "string" &&
    UI_RESOURCE_URI_PATTERN.test(candidate)
    ? candidate
    : null;
}

function isToolResult(value: unknown): value is CallToolResult {
  if (!isRecord(value) || !Array.isArray(value.content)) return false;
  if (value.isError !== undefined && typeof value.isError !== "boolean") {
    return false;
  }
  if (value._meta !== undefined && !isRecord(value._meta)) return false;
  if (
    value.structuredContent !== undefined &&
    !isRecord(value.structuredContent)
  ) {
    return false;
  }
  // Keep the ordinary message path lightweight. The lazy bridge validates the
  // complete MCP result schema before sending any data to the app.
  return value.content.every(
    (block) =>
      isRecord(block) &&
      typeof block.type === "string" &&
      block.type.length > 0 &&
      (block.type !== "text" || typeof block.text === "string"),
  );
}

// @spec MCA-001 — Only explicit frontend integration data enables an MCP app
export function getMCPAppDescriptor(
  event: OpenHandsEvent,
  integrationData?: unknown,
): MCPAppDescriptor | null {
  if (
    event.source !== "environment" ||
    !("observation" in event) ||
    !isRecord(event.observation) ||
    event.observation.kind !== "MCPToolObservation" ||
    !isRecord(integrationData)
  ) {
    return null;
  }

  const { tool, toolInput, toolResult } = integrationData;
  if (
    !isRecord(tool) ||
    typeof tool.name !== "string" ||
    tool.name.trim().length === 0 ||
    !isRecord(tool._meta) ||
    !isRecord(toolInput) ||
    !isToolResult(toolResult)
  ) {
    return null;
  }
  const resourceUri = getResourceUri(tool._meta);
  if (!resourceUri) return null;

  return {
    resourceUri,
    tool: { name: tool.name, _meta: tool._meta },
    toolInput,
    toolResult,
  };
}
