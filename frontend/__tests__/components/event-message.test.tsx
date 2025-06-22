import { afterEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "test-utils";
import { EventMessage } from "#/components/features/chat/event-message";
import { AgentState } from "#/types/agent-state";
import { OpenHandsObservation } from "#/types/core/observations";
import { I18nKey } from "#/i18n/declaration";

// Mock the hooks
vi.mock("#/hooks/query/use-config", () => ({
  useConfig: () => ({
    data: { APP_MODE: "saas" },
  }),
}));

vi.mock("#/hooks/query/use-feedback-exists", () => ({
  useFeedbackExists: (eventId: number | undefined) => ({
    data: { exists: false },
    isLoading: false,
  }),
}));

describe("EventMessage", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render LikertScale for finish action when it's the last message", () => {
    const finishEvent = {
      id: 123,
      source: "agent",
      action: "finish",
      args: {
        message: "Task completed successfully",
        task_completed: "true",
      },
    };

    renderWithProviders(
      <EventMessage
        event={finishEvent}
        hasObservationPair={false}
        isAwaitingUserConfirmation={false}
        isLastMessage={true}
      />
    );

    // Check that the LikertScale component is rendered by looking for the star rating buttons
    expect(screen.getByLabelText("Rate 1 stars")).toBeInTheDocument();
    expect(screen.getByLabelText("Rate 5 stars")).toBeInTheDocument();
  });

  it("should render LikertScale for agent state change to AWAITING_USER_INPUT when it's the last message", () => {
    const stateChangeEvent: OpenHandsObservation = {
      id: 456,
      source: "agent",
      observation: "agent_state_changed",
      args: {
        agent_state: AgentState.AWAITING_USER_INPUT,
        reason: "Waiting for user input",
      },
      content: "",
      extras: {},
    };

    renderWithProviders(
      <EventMessage
        event={stateChangeEvent}
        hasObservationPair={false}
        isAwaitingUserConfirmation={false}
        isLastMessage={true}
      />
    );

    // Check that the LikertScale component is rendered by looking for the star rating buttons
    expect(screen.getByLabelText("Rate 1 stars")).toBeInTheDocument();
    expect(screen.getByLabelText("Rate 5 stars")).toBeInTheDocument();
  });

  it("should render LikertScale for agent state change to ERROR when it's the last message", () => {
    const stateChangeEvent: OpenHandsObservation = {
      id: 789,
      source: "agent",
      observation: "agent_state_changed",
      args: {
        agent_state: AgentState.ERROR,
        reason: "An error occurred",
      },
      content: "",
      extras: {},
    };

    renderWithProviders(
      <EventMessage
        event={stateChangeEvent}
        hasObservationPair={false}
        isAwaitingUserConfirmation={false}
        isLastMessage={true}
      />
    );

    // Check that the LikertScale component is rendered by looking for the star rating buttons
    expect(screen.getByLabelText("Rate 1 stars")).toBeInTheDocument();
    expect(screen.getByLabelText("Rate 5 stars")).toBeInTheDocument();
  });

  it("should NOT render LikertScale for agent state change to RUNNING when it's the last message", () => {
    const stateChangeEvent: OpenHandsObservation = {
      id: 101,
      source: "agent",
      observation: "agent_state_changed",
      args: {
        agent_state: AgentState.RUNNING,
        reason: "Agent is running",
      },
      content: "",
      extras: {},
    };

    renderWithProviders(
      <EventMessage
        event={stateChangeEvent}
        hasObservationPair={false}
        isAwaitingUserConfirmation={false}
        isLastMessage={true}
      />
    );

    // Check that the LikertScale component is NOT rendered
    expect(screen.queryByLabelText("Rate 1 stars")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Rate 5 stars")).not.toBeInTheDocument();
  });
});