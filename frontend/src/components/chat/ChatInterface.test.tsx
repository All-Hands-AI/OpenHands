import React from "react";
import { screen, act, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "test-utils";
import { useTranslation } from "react-i18next";
import ChatInterface from "./ChatInterface";
import Session from "#/services/session";
import ActionType from "#/types/ActionType";
import { addAssistantMessage } from "#/state/chatSlice";
import AgentState from "#/types/AgentState";
import { I18nKey } from "#/i18n/declaration";

// avoid typing side-effect
vi.mock("#/hooks/useTyping", () => ({
  useTyping: vi.fn((text: string) => text),
}));

const sessionSpy = vi.spyOn(Session, "send");
vi.spyOn(Session, "isConnected").mockImplementation(() => true);

// This is for the scrollview ref in Chat.tsx
// TODO: Move this into test setup
HTMLElement.prototype.scrollTo = vi.fn(() => {});

describe("ChatInterface", () => {
  afterEach(() => {
    sessionSpy.mockClear();
  });

  it("should render empty message list and input", () => {
    renderWithProviders(<ChatInterface />);
    expect(screen.queryAllByTestId("message")).toHaveLength(0);
  });

  it("should render the new message the user has typed", () => {
    renderWithProviders(<ChatInterface />, {
      preloadedState: {
        agent: {
          curAgentState: AgentState.INIT,
        },
      },
    });

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "my message" } });
    expect(input).toHaveValue("my message");
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

  it("should send a start event to the Session", () => {
    renderWithProviders(<ChatInterface />, {
      preloadedState: {
        agent: {
          curAgentState: AgentState.INIT,
        },
      },
    });

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "my message" } });
    fireEvent.keyDown(input, { key: "Enter", code: "Enter", charCode: 13 });

    const event = {
      action: ActionType.MESSAGE,
      args: { content: "my message" },
    };
    expect(sessionSpy).toHaveBeenCalledWith(JSON.stringify(event));
  });

  it("should send a user message event to the Session", async () => {
    renderWithProviders(<ChatInterface />, {
      preloadedState: {
        agent: {
          curAgentState: AgentState.AWAITING_USER_INPUT,
        },
      },
    });

    const input = screen.getByRole("textbox");
    await userEvent.type(input, "my message{enter}");

    const event = {
      action: ActionType.MESSAGE,
      args: { content: "my message" },
    };
    expect(sessionSpy).toHaveBeenCalledWith(JSON.stringify(event));
  });

  it("should disable the user input if agent is not initialized", () => {
    renderWithProviders(<ChatInterface />, {
      preloadedState: {
        agent: {
          curAgentState: AgentState.LOADING,
        },
      },
    });

    const { t } = useTranslation();

    const submitButton = screen.getByLabelText(
      t(I18nKey.CHAT_INTERFACE$TOOLTIP_SEND_MESSAGE),
    );

    expect(submitButton).toBeDisabled();
  });
});
