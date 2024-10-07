import { createRemixStub } from "@remix-run/testing";
import { beforeAll, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { ws } from "msw";
import { setupServer } from "msw/node";
import App from "#/routes/app";
import AgentState from "#/types/AgentState";
import { AgentStateChangeObservation } from "#/types/core/observations";

const RemixStub = createRemixStub([{ path: "/app", Component: App }]);

describe.skip("App", () => {
  const agent = ws.link("ws://localhost:3001/ws");
  const server = setupServer();

  beforeAll(() => {
    // mock `dom.scrollTo`
    HTMLElement.prototype.scrollTo = vi.fn().mockImplementation(() => {});
  });

  it("should render", async () => {
    render(<RemixStub initialEntries={["/app"]} />);

    await waitFor(() => {
      expect(screen.getByTestId("app")).toBeInTheDocument();
      expect(
        screen.getByText(/INITIALIZING_AGENT_LOADING_MESSAGE/i),
      ).toBeInTheDocument();
    });
  });

  it("should establish a ws connection and send the init message", async () => {
    server.use(
      agent.addEventListener("connection", ({ client }) => {
        client.send(
          JSON.stringify({
            id: 1,
            cause: 0,
            message: "AGENT_INIT_MESSAGE",
            source: "agent",
            timestamp: new Date().toISOString(),
            observation: "agent_state_changed",
            content: "AGENT_INIT_MESSAGE",
            extras: { agent_state: AgentState.INIT },
          } satisfies AgentStateChangeObservation),
        );
      }),
    );

    render(<RemixStub initialEntries={["/app"]} />);

    await waitFor(() => {
      expect(screen.getByText(/AGENT_INIT_MESSAGE/i)).toBeInTheDocument();
    });
  });
});
