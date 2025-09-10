import { describe, it, expect } from "vitest";
import { getStatusCode } from "../status";
import { AgentState } from "#/types/agent-state";
import { I18nKey } from "#/i18n/declaration";

describe("getStatusCode", () => {
  it("should prioritize agent readiness over stale runtime status", () => {
    // Test case: Agent is ready (AWAITING_USER_INPUT) but runtime status is still starting
    const result = getStatusCode(
      { id: "", message: "", type: "info", status_update: true }, // statusMessage
      "CONNECTED", // webSocketStatus
      "RUNNING", // conversationStatus
      "STATUS$STARTING_RUNTIME", // runtimeStatus (stale)
      AgentState.AWAITING_USER_INPUT, // agentState (ready)
    );

    // Should return agent state message, not runtime status
    expect(result).toBe(
      I18nKey.CHAT_INTERFACE$AGENT_AWAITING_USER_INPUT_MESSAGE,
    );
  });

  it("should show runtime status when agent is not ready", () => {
    // Test case: Agent is loading and runtime is starting
    const result = getStatusCode(
      { id: "", message: "", type: "info", status_update: true }, // statusMessage
      "CONNECTED", // webSocketStatus
      "STARTING", // conversationStatus
      "STATUS$STARTING_RUNTIME", // runtimeStatus
      AgentState.LOADING, // agentState (not ready)
    );

    // Should return runtime status since agent is not ready
    expect(result).toBe("STATUS$STARTING_RUNTIME");
  });

  it("should handle agent running state with stale runtime status", () => {
    // Test case: Agent is running but runtime status is stale
    const result = getStatusCode(
      { id: "", message: "", type: "info", status_update: true }, // statusMessage
      "CONNECTED", // webSocketStatus
      "RUNNING", // conversationStatus
      "STATUS$BUILDING_RUNTIME", // runtimeStatus (stale)
      AgentState.RUNNING, // agentState (ready)
    );

    // Should return agent state message, not runtime status
    expect(result).toBe(I18nKey.CHAT_INTERFACE$AGENT_RUNNING_MESSAGE);
  });

  it("should handle agent finished state with stale runtime status", () => {
    // Test case: Agent is finished but runtime status is stale
    const result = getStatusCode(
      { id: "", message: "", type: "info", status_update: true }, // statusMessage
      "CONNECTED", // webSocketStatus
      "RUNNING", // conversationStatus
      "STATUS$SETTING_UP_WORKSPACE", // runtimeStatus (stale)
      AgentState.FINISHED, // agentState (ready)
    );

    // Should return agent state message, not runtime status
    expect(result).toBe(I18nKey.CHAT_INTERFACE$AGENT_FINISHED_MESSAGE);
  });

  it("should still respect stopped states", () => {
    // Test case: Runtime is stopped - should always show stopped
    const result = getStatusCode(
      { id: "", message: "", type: "info", status_update: true }, // statusMessage
      "CONNECTED", // webSocketStatus
      "STOPPED", // conversationStatus
      "STATUS$STOPPED", // runtimeStatus
      AgentState.RUNNING, // agentState
    );

    // Should return stopped status regardless of agent state
    expect(result).toBe(I18nKey.CHAT_INTERFACE$STOPPED);
  });

  it("should handle null agent state with runtime status", () => {
    // Test case: No agent state, runtime is starting
    const result = getStatusCode(
      { id: "", message: "", type: "info", status_update: true }, // statusMessage
      "CONNECTED", // webSocketStatus
      "STARTING", // conversationStatus
      "STATUS$STARTING_RUNTIME", // runtimeStatus
      null, // agentState
    );

    // Should return runtime status since no agent state
    expect(result).toBe("STATUS$STARTING_RUNTIME");
  });
});
