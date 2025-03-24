import { describe, it, expect } from "vitest";
import { AgentState } from "#/types/agent-state";

// Simple test to verify the AgentState enum
describe("AgentState", () => {
  it("should have the correct values", () => {
    expect(AgentState.LOADING).toBe("loading");
    expect(AgentState.RUNNING).toBe("running");
    expect(AgentState.AWAITING_USER_INPUT).toBe("awaiting_user_input");
  });
});