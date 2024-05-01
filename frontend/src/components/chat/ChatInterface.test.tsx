import React from "react";
import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { act } from "react-dom/test-utils";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "test-utils";
import ChatInterface from "./ChatInterface";
import Socket from "#/services/socket";
import ActionType from "#/types/ActionType";
import { addAssistantMessage } from "#/state/chat";

const socketSpy = vi.spyOn(Socket, "send");

describe("ChatInterface", () => {
  it("should render the messages and input", () => {
    renderWithProviders(<ChatInterface />);
    expect(screen.queryAllByTestId("message")).toHaveLength(0);
  });

  it("should render the new message the user has typed", () => {
    renderWithProviders(<ChatInterface />);

    const input = screen.getByRole("textbox");

    act(() => {
      userEvent.type(input, "my message{enter}");
    });

    expect(screen.getByText("my message")).toBeInTheDocument();
  });

  it("should render user and assistant messages", () => {
    const { store } = renderWithProviders(<ChatInterface />, {
      preloadedState: {
        tempChat: {
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

  it("should send the a user message event to the Socket", () => {
    renderWithProviders(<ChatInterface />);
    const input = screen.getByRole("textbox");
    act(() => {
      userEvent.type(input, "my message{enter}");
    });

    const event = { action: ActionType.START, args: { task: "my message" } };
    expect(socketSpy).toHaveBeenCalledWith(JSON.stringify(event));
  });
});
