import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { 
  AppStateProvider, 
  useAgentState, 
  useMetrics, 
  useStatusMessage, 
  useInitialQuery 
} from "#/hooks/query/simplified/use-state-context";
import { AgentState } from "#/types/agent-state";

// Test component that uses the hooks
function TestComponent() {
  const { curAgentState, setCurrentAgentState } = useAgentState();
  const { metrics, setMetrics } = useMetrics();
  const { statusMessage, setStatusMessage } = useStatusMessage();
  const { 
    files, 
    initialPrompt, 
    selectedRepository, 
    setFiles, 
    setInitialPrompt, 
    setSelectedRepository 
  } = useInitialQuery();

  return (
    <div>
      <div data-testid="agent-state">{curAgentState}</div>
      <button 
        data-testid="set-agent-ready" 
        onClick={() => setCurrentAgentState(AgentState.READY)}
      >
        Set Ready
      </button>

      <div data-testid="metrics-cost">{metrics.cost === null ? "null" : metrics.cost}</div>
      <button 
        data-testid="set-metrics" 
        onClick={() => setMetrics({ cost: 0.25, usage: { prompt_tokens: 100, completion_tokens: 50, total_tokens: 150 } })}
      >
        Set Metrics
      </button>

      <div data-testid="status-message">{statusMessage.message}</div>
      <button 
        data-testid="set-status" 
        onClick={() => setStatusMessage({ status_update: true, type: "info", id: "test", message: "Test Message" })}
      >
        Set Status
      </button>

      <div data-testid="files">{files.length}</div>
      <div data-testid="initial-prompt">{initialPrompt || "null"}</div>
      <div data-testid="selected-repo">{selectedRepository || "null"}</div>
      <button 
        data-testid="set-files" 
        onClick={() => setFiles(["file1", "file2"])}
      >
        Set Files
      </button>
      <button 
        data-testid="set-prompt" 
        onClick={() => setInitialPrompt("Test Prompt")}
      >
        Set Prompt
      </button>
      <button 
        data-testid="set-repo" 
        onClick={() => setSelectedRepository("test/repo")}
      >
        Set Repo
      </button>
    </div>
  );
}

describe("AppStateContext", () => {
  it("should provide default state values", () => {
    render(
      <AppStateProvider>
        <TestComponent />
      </AppStateProvider>
    );

    expect(screen.getByTestId("agent-state").textContent).toBe(AgentState.LOADING.toString());
    expect(screen.getByTestId("metrics-cost").textContent).toBe("null");
    expect(screen.getByTestId("status-message").textContent).toBe("");
    expect(screen.getByTestId("files").textContent).toBe("0");
    expect(screen.getByTestId("initial-prompt").textContent).toBe("null");
    expect(screen.getByTestId("selected-repo").textContent).toBe("null");
  });

  it("should update agent state", () => {
    render(
      <AppStateProvider>
        <TestComponent />
      </AppStateProvider>
    );

    fireEvent.click(screen.getByTestId("set-agent-ready"));
    expect(screen.getByTestId("agent-state").textContent).toBe(AgentState.READY.toString());
  });

  it("should update metrics", () => {
    render(
      <AppStateProvider>
        <TestComponent />
      </AppStateProvider>
    );

    fireEvent.click(screen.getByTestId("set-metrics"));
    expect(screen.getByTestId("metrics-cost").textContent).toBe("0.25");
  });

  it("should update status message", () => {
    render(
      <AppStateProvider>
        <TestComponent />
      </AppStateProvider>
    );

    fireEvent.click(screen.getByTestId("set-status"));
    expect(screen.getByTestId("status-message").textContent).toBe("Test Message");
  });

  it("should update initial query state", () => {
    render(
      <AppStateProvider>
        <TestComponent />
      </AppStateProvider>
    );

    fireEvent.click(screen.getByTestId("set-files"));
    fireEvent.click(screen.getByTestId("set-prompt"));
    fireEvent.click(screen.getByTestId("set-repo"));

    expect(screen.getByTestId("files").textContent).toBe("2");
    expect(screen.getByTestId("initial-prompt").textContent).toBe("Test Prompt");
    expect(screen.getByTestId("selected-repo").textContent).toBe("test/repo");
  });
});