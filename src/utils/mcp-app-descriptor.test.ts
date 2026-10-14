import { describe, expect, it } from "vitest";
import type { OpenHandsEvent } from "#/types/agent-server/core";
import type { MCPAppIntegrationData } from "#/types/mcp-app";
import { getMCPAppDescriptor } from "./mcp-app-descriptor";

function makeEvent(overrides: Record<string, unknown> = {}): OpenHandsEvent {
  return {
    id: "event-chart-result",
    timestamp: "2026-10-13T00:00:00Z",
    source: "environment",
    action_id: "event-chart-action",
    tool_call_id: "call-chart",
    tool_name: "analytics_chart",
    observation: {
      kind: "MCPToolObservation",
      content: [{ type: "text", text: "Chart ready" }],
      is_error: false,
      tool_name: "analytics_chart",
    },
    ...overrides,
  } as OpenHandsEvent;
}

const integrationData: MCPAppIntegrationData = {
  tool: { name: "chart", _meta: { ui: { resourceUri: "ui://chart" } } },
  toolInput: { symbol: "OPEN" },
  toolResult: {
    content: [{ type: "text", text: "Chart ready" }],
    structuredContent: { points: [1, 2] },
    _meta: { privateSelection: "OPEN" },
  },
};

// @spec MCA-001 — MCP app descriptors preserve ordinary tool-result fallback
describe("getMCPAppDescriptor", () => {
  it("normalizes independent presentation data without confusing the original tool name with the agent alias", () => {
    const event = makeEvent();
    const descriptor = getMCPAppDescriptor(event, integrationData);

    expect(descriptor).toEqual({
      resourceUri: "ui://chart",
      ...integrationData,
    });
    expect(event).toEqual(makeEvent());
  });

  it("ignores an unpublished App field on the canonical event", () => {
    const event = makeEvent({ mcp_app: integrationData });

    expect(getMCPAppDescriptor(event)).toBeNull();
    expect(getMCPAppDescriptor(event, null)).toBeNull();
  });

  it("accepts legacy metadata only when nested UI metadata is absent", () => {
    const data = {
      ...integrationData,
      tool: { name: "chart", _meta: { "ui/resourceUri": "ui://legacy" } },
    };

    expect(getMCPAppDescriptor(makeEvent(), data)?.resourceUri).toBe(
      "ui://legacy",
    );
  });

  it("prefers nested metadata over a different legacy URI", () => {
    const data = {
      ...integrationData,
      tool: {
        name: "chart",
        _meta: {
          ui: { resourceUri: "ui://nested" },
          "ui/resourceUri": "ui://legacy",
        },
      },
    };

    expect(getMCPAppDescriptor(makeEvent(), data)?.resourceUri).toBe(
      "ui://nested",
    );
  });

  it.each([
    null,
    [],
    {},
    { resourceUri: "" },
    { resourceUri: "https://example.com/chart" },
    { resourceUri: "ui://" },
    { resourceUri: "ui://chart with spaces" },
    { resourceUri: 7 },
  ])(
    "rejects invalid nested metadata without falling back to legacy (%j)",
    (ui) => {
      const data = {
        ...integrationData,
        tool: { name: "chart", _meta: { ui, "ui/resourceUri": "ui://legacy" } },
      };

      expect(getMCPAppDescriptor(makeEvent(), data)).toBeNull();
    },
  );

  it.each([undefined, null, []])(
    "leaves missing presentation data on the existing fallback path (%j)",
    (data) => {
      expect(getMCPAppDescriptor(makeEvent(), data)).toBeNull();
    },
  );

  it.each([
    { source: "agent" },
    { observation: { kind: "TerminalObservation" } },
  ])(
    "leaves unrelated events on the existing fallback path (%j)",
    (overrides) => {
      expect(
        getMCPAppDescriptor(makeEvent(overrides), integrationData),
      ).toBeNull();
    },
  );

  it.each([
    { tool: null },
    { tool: { name: "", _meta: { ui: { resourceUri: "ui://chart" } } } },
    { toolInput: [] },
    { toolInput: null },
    { toolResult: null },
    { toolResult: { content: null } },
    { toolResult: { content: [null] } },
    { toolResult: { content: [{}] } },
    { toolResult: { content: [{ type: "text", text: 3 }] } },
    { toolResult: { content: [], isError: "false" } },
    { toolResult: { content: [], structuredContent: [] } },
    { toolResult: { content: [], _meta: [] } },
  ])(
    "rejects malformed integration data before creating an app (%j)",
    (overrides) => {
      expect(
        getMCPAppDescriptor(makeEvent(), { ...integrationData, ...overrides }),
      ).toBeNull();
    },
  );
});
