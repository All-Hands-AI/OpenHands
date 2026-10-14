import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "test-utils";
import { resolveVisualizerBody } from "#/components/features/chat/tool-visualizers/dispatcher";
import { GenericEventMessageWrapper } from "#/components/conversation-events/chat/event-message-components/generic-event-message-wrapper";
import type { ObservationEvent } from "#/types/agent-server/core";
import type { MCPToolObservation } from "#/types/agent-server/core/base/observation";
import type { MCPAppArtifacts } from "#/types/mcp-app";
import { MCPAppHostProvider } from "#/components/features/mcp-apps/mcp-app-host-context";
import { getMCPAppDescriptor } from "#/utils/mcp-app-descriptor";

vi.mock("#/components/features/mcp-apps/mcp-app-artifact", () => ({
  MCPAppArtifact: ({ descriptor }: { descriptor: { resourceUri: string } }) => (
    <div data-testid="mcp-app-artifact">{descriptor.resourceUri}</div>
  ),
}));

const makeObservation = (): ObservationEvent<MCPToolObservation> => ({
  id: "mcp-result",
  timestamp: "2026-10-13T00:00:00Z",
  source: "environment" as const,
  tool_name: "show_chart",
  tool_call_id: "chart-call",
  action_id: "chart-action",
  observation: {
    kind: "MCPToolObservation" as const,
    tool_name: "show_chart",
    content: [{ type: "text" as const, text: "Chart data ready." }],
    is_error: false,
  },
});

const makeArtifacts = (
  eventId: string,
  resourceUri?: string,
): MCPAppArtifacts =>
  resourceUri
    ? new Map([
        [
          eventId,
          {
            tool: { name: "show_chart", _meta: { ui: { resourceUri } } },
            toolInput: { symbol: "TEST" },
            toolResult: {
              content: [{ type: "text", text: "Chart data ready." }],
            },
          },
        ],
      ])
    : new Map();

describe("MCP app conversation integration", () => {
  // @spec MCA-001 — Invalid or absent App metadata keeps existing MCP markdown.
  it.each([undefined, "https://example.com/chart"])(
    "keeps the existing markdown fallback when there is no valid UI resource (%s)",
    async (resourceUri) => {
      const user = userEvent.setup();
      const event = makeObservation();
      const artifacts = makeArtifacts(event.id, resourceUri);
      const descriptor = getMCPAppDescriptor(event, artifacts.get(event.id));

      expect(resolveVisualizerBody(event, undefined, descriptor)).toBeNull();
      const { container } = renderWithProviders(
        <MCPAppHostProvider host={null} scope={null} artifacts={artifacts}>
          <GenericEventMessageWrapper event={event} isLastMessage />
        </MCPAppHostProvider>,
      );
      expect(container).not.toHaveTextContent("Chart data ready.");
      await user.click(screen.getByRole("button", { name: "BUTTON$EXPAND" }));
      expect(container).toHaveTextContent("Chart data ready.");
      expect(screen.queryByTestId("mcp-app-artifact")).not.toBeInTheDocument();
    },
  );

  // @spec MCA-002 — App artifacts and original output are visible inline.
  it("shows the app and the original tool result without expanding its card", () => {
    const event = makeObservation();

    renderWithProviders(
      <MCPAppHostProvider
        host={null}
        scope={null}
        artifacts={makeArtifacts(event.id, "ui://chart/view")}
      >
        <GenericEventMessageWrapper event={event} isLastMessage />
      </MCPAppHostProvider>,
    );

    expect(screen.getByTestId("mcp-app-artifact")).toHaveTextContent(
      "ui://chart/view",
    );
    expect(screen.getByText("Chart data ready.")).toBeInTheDocument();
  });

  it("expands an existing MCP card when its independent sidecar arrives", () => {
    const event = makeObservation();
    const renderCard = (artifacts?: MCPAppArtifacts) => (
      <MCPAppHostProvider host={null} scope={null} artifacts={artifacts}>
        <GenericEventMessageWrapper event={event} isLastMessage />
      </MCPAppHostProvider>
    );
    const { rerender } = renderWithProviders(renderCard());
    expect(screen.queryByTestId("mcp-app-artifact")).not.toBeInTheDocument();

    rerender(renderCard(makeArtifacts(event.id, "ui://chart/view")));

    expect(screen.getByTestId("mcp-app-artifact")).toHaveTextContent(
      "ui://chart/view",
    );
    expect(screen.getByText("Chart data ready.")).toBeInTheDocument();
  });

  it("ignores an App-shaped wire field without an independently owned sidecar", async () => {
    const user = userEvent.setup();
    const observation = makeObservation();
    const event = {
      ...observation,
      mcp_app: makeArtifacts(observation.id, "ui://untrusted").get(
        observation.id,
      ),
    };

    renderWithProviders(
      <GenericEventMessageWrapper event={event} isLastMessage />,
    );
    expect(screen.queryByTestId("mcp-app-artifact")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "BUTTON$EXPAND" }));
    expect(screen.getByText("Chart data ready.")).toBeInTheDocument();
  });
});
