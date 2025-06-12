import { describe, expect, it } from "vitest";
import { AxiosError } from "axios";
import {
  isAxiosErrorWithErrorField,
  isAxiosErrorWithMessageField,
  isOpenHandsAction,
  isOpenHandsObservation,
  isUserMessage,
  isAssistantMessage,
  isErrorObservation,
  isCommandAction,
  isAgentStateChangeObservation,
  isCommandObservation,
  isFinishAction,
  isSystemMessage,
  isRejectObservation,
  isMcpObservation,
  isStatusUpdate,
} from "../guards";

describe("Axios Error Type Guards", () => {
  it("should correctly identify AxiosError with error field", () => {
    const error = new AxiosError();
    error.response = {
      data: { error: "test error" },
      status: 400,
      statusText: "Bad Request",
      headers: {},
      config: {
        headers: {},
      },
    };

    expect(isAxiosErrorWithErrorField(error)).toBe(true);
  });

  it("should correctly identify AxiosError with message field", () => {
    const error = new AxiosError();
    error.response = {
      data: { message: "test message" },
      status: 400,
      statusText: "Bad Request",
      headers: {},
      config: {
        headers: {},
      },
    };

    expect(isAxiosErrorWithMessageField(error)).toBe(true);
  });

  it("should reject AxiosError without error field", () => {
    const error = new AxiosError();
    error.response = {
      data: { other: "field" },
      status: 400,
      statusText: "Bad Request",
      headers: {},
      config: {
        headers: {},
      },
    };

    expect(isAxiosErrorWithErrorField(error)).toBe(false);
  });

  it("should reject AxiosError without message field", () => {
    const error = new AxiosError();
    error.response = {
      data: { other: "field" },
      status: 400,
      statusText: "Bad Request",
      headers: {},
      config: {
        headers: {},
      },
    };

    expect(isAxiosErrorWithMessageField(error)).toBe(false);
  });
});

describe("OpenHands Event Type Guards", () => {
  it("should correctly identify OpenHandsAction", () => {
    const event = {
      action: "message" as const,
      source: "agent" as const,
      args: {},
      id: 1,
      message: "test message",
      timestamp: new Date().toISOString(),
    };

    expect(isOpenHandsAction(event)).toBe(true);
  });

  it("should correctly identify OpenHandsObservation", () => {
    const event = {
      observation: "error" as const,
      source: "agent" as const,
      extras: {},
      cause: 1,
      content: "test content",
      id: 1,
      message: "test message",
      timestamp: new Date().toISOString(),
    };

    expect(isOpenHandsObservation(event)).toBe(true);
  });

  it("should correctly identify UserMessage", () => {
    const event = {
      action: "message" as const,
      source: "user" as const,
      args: {},
      id: 1,
      message: "test message",
      timestamp: new Date().toISOString(),
    };

    expect(isUserMessage(event)).toBe(true);
  });

  it("should correctly identify AssistantMessage", () => {
    const event = {
      action: "message" as const,
      source: "agent" as const,
      args: {},
      id: 1,
      message: "test message",
      timestamp: new Date().toISOString(),
    };

    expect(isAssistantMessage(event)).toBe(true);
  });

  it("should correctly identify ErrorObservation", () => {
    const event = {
      observation: "error" as const,
      source: "agent" as const,
      extras: {},
      cause: 1,
      content: "test content",
      id: 1,
      message: "test message",
      timestamp: new Date().toISOString(),
    };

    expect(isErrorObservation(event)).toBe(true);
  });

  it("should correctly identify CommandAction", () => {
    const event = {
      action: "run" as const,
      source: "agent" as const,
      args: {
        command: "test",
      },
      id: 1,
      message: "test message",
      timestamp: new Date().toISOString(),
    };

    expect(isCommandAction(event)).toBe(true);
  });

  it("should correctly identify AgentStateChangeObservation", () => {
    const event = {
      observation: "agent_state_changed" as const,
      source: "agent" as const,
      extras: {},
      cause: 1,
      content: "test content",
      id: 1,
      message: "test message",
      timestamp: new Date().toISOString(),
    };

    expect(isAgentStateChangeObservation(event)).toBe(true);
  });

  it("should correctly identify CommandObservation", () => {
    const event = {
      observation: "run" as const,
      source: "agent" as const,
      extras: {},
      cause: 1,
      content: "test content",
      id: 1,
      message: "test message",
      timestamp: new Date().toISOString(),
    };

    expect(isCommandObservation(event)).toBe(true);
  });

  it("should correctly identify FinishAction", () => {
    const event = {
      action: "finish" as const,
      source: "agent" as const,
      args: {},
      id: 1,
      message: "test message",
      timestamp: new Date().toISOString(),
    };

    expect(isFinishAction(event)).toBe(true);
  });

  it("should correctly identify SystemMessage", () => {
    const event = {
      action: "system" as const,
      source: "agent" as const,
      args: {},
      id: 1,
      message: "test message",
      timestamp: new Date().toISOString(),
    };

    expect(isSystemMessage(event)).toBe(true);
  });

  it("should correctly identify RejectObservation", () => {
    const event = {
      observation: "user_rejected" as const,
      source: "agent" as const,
      extras: {},
      cause: 1,
      content: "test content",
      id: 1,
      message: "test message",
      timestamp: new Date().toISOString(),
    };

    expect(isRejectObservation(event)).toBe(true);
  });

  it("should correctly identify MCPObservation", () => {
    const event = {
      observation: "mcp" as const,
      source: "agent" as const,
      extras: {},
      cause: 1,
      content: "test content",
      id: 1,
      message: "test message",
      timestamp: new Date().toISOString(),
    };

    expect(isMcpObservation(event)).toBe(true);
  });

  it("should correctly identify StatusUpdate", () => {
    const event = {
      status_update: true as const,
      type: "error" as const,
      id: 1,
      message: "test message",
    };

    expect(isStatusUpdate(event)).toBe(true);
  });
});
