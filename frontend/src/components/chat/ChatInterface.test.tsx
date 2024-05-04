import React from "react";
import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { act } from "react-dom/test-utils";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "test-utils";
import ChatInterface from "./ChatInterface";
import Socket from "#/services/socket";
import ActionType from "#/types/ActionType";
import { addAssistantMessage } from "#/state/chatSlice";
import AgentTaskState from "#/types/AgentTaskState";

// avoid typing side-effect
vi.mock("#/hooks/useTyping", () => ({
  useTyping: vi.fn((text: string) => text),
}));

const socketSpy = vi.spyOn(Socket, "send");

// This is for the scrollview ref in Chat.tsx
// TODO: Move this into test setup
HTMLElement.prototype.scrollIntoView = vi.fn();

const renderChatInterface = () =>
  renderWithProviders(<ChatInterface />, {
    preloadedState: {
      task: {
        initialized: true,
        completed: false,
      },
    },
  });

describe("ChatInterface", () => {
  it("should render the messages and input", () => {
    renderChatInterface();
    expect(screen.queryAllByTestId("message")).toHaveLength(1); // initial welcome message only
  });

  it("should render the new message the user has typed", async () => {
    renderChatInterface();

    const input = screen.getByRole("textbox");

    act(() => {
      userEvent.type(input, "my message{enter}");
    });

    expect(screen.getByText("my message")).toBeInTheDocument();
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
      store.dispatch(addAssistantMessage("Hello to you!"));
    });

    expect(screen.getAllByTestId("message")).toHaveLength(2);
    expect(screen.getByText("Hello to you!")).toBeInTheDocument();
  });

  it("should send the a start event to the Socket", () => {
    renderWithProviders(<ChatInterface />, {
      preloadedState: {
        task: {
          initialized: true,
          completed: false,
        },
        agent: {
          curTaskState: AgentTaskState.INIT,
        },
      },
    });

    const input = screen.getByRole("textbox");
    act(() => {
      userEvent.type(input, "my message{enter}");
    });

    const event = { action: ActionType.START, args: { task: "my message" } };
    expect(socketSpy).toHaveBeenCalledWith(JSON.stringify(event));
  });

  it("should send the a user message event to the Socket", () => {
    renderWithProviders(<ChatInterface />, {
      preloadedState: {
        task: {
          initialized: true,
          completed: false,
        },
        agent: {
          curTaskState: AgentTaskState.AWAITING_USER_INPUT,
        },
      },
    });

    const input = screen.getByRole("textbox");
    act(() => {
      userEvent.type(input, "my message{enter}");
    });

    const event = {
      action: ActionType.USER_MESSAGE,
      args: { message: "my message" },
    };
    expect(socketSpy).toHaveBeenCalledWith(JSON.stringify(event));
  });

  it("should disable the user input if agent is not initialized", () => {
    renderWithProviders(<ChatInterface />, {
      preloadedState: {
        task: {
          initialized: false,
          completed: false,
        },
      },
    });

    const submitButton = screen.getByLabelText(/send message/i);

    expect(submitButton).toBeDisabled();
  });
});
