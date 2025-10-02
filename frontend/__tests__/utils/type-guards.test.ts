import { describe, expect, it } from "vitest";
import {
  ActionEvent,
  MessageEvent,
  ObservationEvent,
  SecurityRisk,
} from "#/types/v1/core";
import { isObservationEvent } from "#/types/v1/type-guards";

describe("isObservationEvent", () => {
  const mockObservationEvent: ObservationEvent = {
    id: "test-observation-1",
    timestamp: Date.now().toString(),
    source: "environment",
    tool_name: "execute_bash",
    tool_call_id: "call_123",
    observation: {
      kind: "ExecuteBashObservation",
      output: "hello\n",
      command: "echo hello",
      exit_code: 0,
      error: false,
      timeout: false,
      metadata: {
        exit_code: 0,
        pid: 12345,
        username: "user",
        hostname: "localhost",
        working_dir: "/home/user",
        py_interpreter_path: null,
        prefix: "",
        suffix: "",
      },
    },
    action_id: "test-action-1",
  };

  const mockActionEvent: ActionEvent = {
    id: "test-action-1",
    timestamp: Date.now().toString(),
    source: "agent",
    thought: [{ type: "text", text: "I need to execute a bash command" }],
    thinking_blocks: [],
    action: {
      kind: "ExecuteBashAction",
      command: "echo hello",
      is_input: false,
      timeout: null,
      reset: false,
    },
    tool_name: "execute_bash",
    tool_call_id: "call_123",
    tool_call: {
      id: "call_123",
      type: "function",
      function: {
        name: "execute_bash",
        arguments: '{"command": "echo hello"}',
      },
    },
    llm_response_id: "response_123",
    security_risk: SecurityRisk.UNKNOWN,
  };

  const mockMessageEvent: MessageEvent = {
    id: "test-event-1",
    timestamp: Date.now().toString(),
    source: "user",
    llm_message: {
      role: "user",
      content: [{ type: "text", text: "Hello, world!" }],
    },
    activated_microagents: [],
    extended_content: [],
  };

  it("should return true for observation events", () => {
    expect(isObservationEvent(mockObservationEvent)).toBe(true);
  });

  it("should return false for action events", () => {
    expect(isObservationEvent(mockActionEvent)).toBe(false);
  });

  it("should return false for message events", () => {
    expect(isObservationEvent(mockMessageEvent)).toBe(false);
  });

  it("should return false for events with environment source but missing action_id", () => {
    const eventWithoutActionId = {
      ...mockObservationEvent,
      action_id: undefined,
    };
    // Remove action_id property completely
    delete (eventWithoutActionId as any).action_id;

    expect(isObservationEvent(eventWithoutActionId as any)).toBe(false);
  });

  it("should return false for events with environment source but missing observation", () => {
    const eventWithoutObservation = {
      ...mockObservationEvent,
      observation: undefined,
    };
    // Remove observation property completely
    delete (eventWithoutObservation as any).observation;

    expect(isObservationEvent(eventWithoutObservation as any)).toBe(false);
  });

  it("should return false for events with action_id and observation but wrong source", () => {
    const eventWithWrongSource = {
      ...mockObservationEvent,
      source: "agent" as const,
    };

    expect(isObservationEvent(eventWithWrongSource as any)).toBe(false);
  });
});
