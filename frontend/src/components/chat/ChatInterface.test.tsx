import React from "react";
import { screen, act } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "test-utils";
import ChatInterface from "./ChatInterface";
import Session from "#/services/session";
import ActionType from "#/types/ActionType";
import { addAssistantMessage } from "#/state/chatSlice";
import AgentState from "#/types/AgentState";

// This is for the scrollview ref in Chat.tsx
// TODO: Move this into test setup
HTMLElement.prototype.scrollTo = vi.fn().mockImplementation(() => {});

describe("ChatInterface", () => {
  const sessionSendSpy = vi.spyOn(Session, "send");
  vi.spyOn(Session, "isConnected").mockReturnValue(true);

  const userMessageEvent = {
    action: ActionType.MESSAGE,
    args: { content: "my message" },
  };

  afterEach(() => {
    sessionSendSpy.mockClear();
  });

  it("should render empty message list and input", () => {
    renderWithProviders(<ChatInterface />);
    expect(screen.queryAllByTestId("message")).toHaveLength(0);
  });

  it("should render user and assistant messages", () => {
    const { store } = renderWithProviders(<ChatInterface />, {
      preloadedState: {
        chat: {
          messages: [{ sender: "user", content: "Hello" }],
        },
      },
    });

    expect(screen.getAllByTestId("message")).toHaveLength(1);
    expect(screen.getByText("Hello")).toBeInTheDocument();

    act(() => {
      // simulate assistant response
      store.dispatch(addAssistantMessage("Hello to you!"));
    });

    expect(screen.getAllByTestId("message")).toHaveLength(2);
    expect(screen.getByText("Hello to you!")).toBeInTheDocument();
  });

  it("should send the user message as an event to the Session when the agent state is INIT", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ChatInterface />, {
      preloadedState: {
        agent: {
          curAgentState: AgentState.INIT,
        },
      },
    });

    const input = screen.getByRole("textbox");
    await user.type(input, "my message");
    await user.keyboard("{Enter}");

    expect(sessionSendSpy).toHaveBeenCalledWith(
      JSON.stringify(userMessageEvent),
    );
  });

  it("should send the user message as an event to the Session when the agent state is AWAITING_USER_INPUT", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ChatInterface />, {
      preloadedState: {
        agent: {
          curAgentState: AgentState.AWAITING_USER_INPUT,
        },
      },
    });

    const input = screen.getByRole("textbox");
    await user.type(input, "my message");
    await user.keyboard("{Enter}");

    expect(sessionSendSpy).toHaveBeenCalledWith(
      JSON.stringify(userMessageEvent),
    );
  });

  it("should disable the user input if agent is not initialized", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ChatInterface />, {
      preloadedState: {
        agent: {
          curAgentState: AgentState.LOADING,
        },
      },
    });

    const input = screen.getByRole("textbox");
    await user.type(input, "my message");
    await user.keyboard("{Enter}");
    const submitButton = screen.getByLabelText(
      "CHAT_INTERFACE$TOOLTIP_SEND_MESSAGE",
    );

    expect(submitButton).toBeDisabled();
    expect(sessionSendSpy).not.toHaveBeenCalled();
  });

  it.todo("test scroll-related behaviour");
});
