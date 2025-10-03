import { render, screen } from "@testing-library/react";
import { JupyterEditor } from "#/components/features/jupyter/jupyter";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { AgentState } from "#/types/agent-state";
import { useAgentStore } from "#/stores/agent-store";
import { useJupyterStore } from "#/state/jupyter-store";

// Mock the agent store
vi.mock("#/stores/agent-store", () => ({
  useAgentStore: vi.fn(),
}));

// Mock react-i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe("JupyterEditor", () => {
  beforeEach(() => {
    // Reset the Zustand store before each test
    useJupyterStore.setState({
      cells: Array(20).fill({
        content: "Test cell content",
        type: "input",
        imageUrls: undefined,
      }),
    });
  });

  it("should have a scrollable container", () => {
    // Mock agent store to return RUNNING state (not in RUNTIME_INACTIVE_STATES)
    vi.mocked(useAgentStore).mockReturnValue({
      curAgentState: AgentState.RUNNING,
      setCurrentAgentState: vi.fn(),
      reset: vi.fn(),
    });

    render(
      <div style={{ height: "100vh" }}>
        <JupyterEditor maxWidth={800} />
      </div>,
    );

    const container = screen.getByTestId("jupyter-container");
    expect(container).toHaveClass("flex-1 overflow-y-auto");
  });
});
