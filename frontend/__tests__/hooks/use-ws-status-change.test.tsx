import { renderHook } from "@testing-library/react";
import { useWSStatusChange } from "#/routes/_oh.app/hooks/use-ws-status-change";
import { WsClientProviderStatus } from "#/context/ws-client-provider";
import { AgentState } from "#/types/agent-state";
import { setCurrentAgentState } from "#/state/agent-slice";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import * as wsClientProvider from "#/context/ws-client-provider";
import * as authContext from "#/context/auth-context";
import * as reactRedux from "react-redux";

// Mock the dependencies
vi.mock("#/context/ws-client-provider");
vi.mock("#/context/auth-context");
vi.mock("react-redux");

describe("useWSStatusChange", () => {
  const mockDispatch = vi.fn();
  const mockUseWsClient = vi.fn();
  const mockUseSelector = vi.fn();

  beforeEach(() => {
    vi.spyOn(reactRedux, "useDispatch").mockReturnValue(mockDispatch);
    vi.spyOn(wsClientProvider, "useWsClient").mockReturnValue({
      status: WsClientProviderStatus.CONNECTED,
      send: vi.fn(),
    });
    vi.spyOn(authContext, "useAuth").mockReturnValue({
      gitHubToken: null,
    });
    vi.spyOn(reactRedux, "useSelector").mockImplementation((selector) => {
      if (selector.name === "selectedRepository") {
        return { selectedRepository: null };
      }
      return {
        curAgentState: AgentState.RUNNING,
        files: [],
        importedProjectZip: null,
        initialQuery: "",
      };
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should set agent state to DISCONNECTED when websocket disconnects", () => {
    // Initial render with connected status
    const { rerender } = renderHook(() => useWSStatusChange());

    // Update websocket status to disconnected
    vi.spyOn(wsClientProvider, "useWsClient").mockReturnValue({
      status: WsClientProviderStatus.DISCONNECTED,
      send: vi.fn(),
    });

    // Rerender the hook with new status
    rerender();

    // Verify that the agent state was set to DISCONNECTED
    expect(mockDispatch).toHaveBeenCalledWith(
      setCurrentAgentState(AgentState.DISCONNECTED),
    );
  });
});
