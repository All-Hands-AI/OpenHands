import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { JupyterEditor } from "#/components/features/jupyter/jupyter";
import { jupyterReducer } from "#/state/jupyter-slice";
import { vi, describe, it, expect } from "vitest";
import { AgentState } from "#/types/agent-state";
import { useAgentStore } from "#/stores/agent-store";

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
  const mockStore = configureStore({
    reducer: {
      jupyter: jupyterReducer,
    },
    preloadedState: {
      jupyter: {
        cells: Array(20).fill({
          content: "Test cell content",
          type: "input",
          output: "Test output",
        }),
      },
    },
  });

  it("should have a scrollable container", () => {
    // Mock agent store to return RUNNING state (not in RUNTIME_INACTIVE_STATES)
    vi.mocked(useAgentStore).mockReturnValue({
      curAgentState: AgentState.RUNNING,
      setCurrentAgentState: vi.fn(),
      reset: vi.fn(),
    });

    render(
      <Provider store={mockStore}>
        <div style={{ height: "100vh" }}>
          <JupyterEditor maxWidth={800} />
        </div>
      </Provider>,
    );

    const container = screen.getByTestId("jupyter-container");
    expect(container).toHaveClass("flex-1 overflow-y-auto");
  });
});
