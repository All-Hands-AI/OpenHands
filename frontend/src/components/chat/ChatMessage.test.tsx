import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import React from "react";
import userEvent from "@testing-library/user-event";
import ChatMessage from "./ChatMessage";
import toast from "#/utils/toast";

describe("Message", () => {
  it("should render a user message", () => {
    render(
      <ChatMessage
        message={{
          sender: "user",
          content: "Hello",
          imageUrls: [],
          timestamp: new Date().toISOString(),
        }}
        isLastMessage={false}
      />,
    );

    expect(screen.getByTestId("article")).toBeInTheDocument();
    expect(screen.getByTestId("article")).toHaveClass("self-end"); // user message should be on the right side
  });

  it("should render an assistant message", () => {
    render(
      <ChatMessage
        message={{
          sender: "assistant",
          content: "Hi",
          imageUrls: [],
          timestamp: new Date().toISOString(),
        }}
        isLastMessage={false}
      />,
    );

    expect(screen.getByTestId("article")).toBeInTheDocument();
    expect(screen.getByTestId("article")).not.toHaveClass("self-end"); // assistant message should be on the left side
  });

  it("should render markdown content", () => {
    render(
      <ChatMessage
        message={{
          sender: "user",
          content: "```js\nconsole.log('Hello')\n```",
          imageUrls: [],
          timestamp: new Date().toISOString(),
        }}
        isLastMessage={false}
      />,
    );

    // SyntaxHighlighter breaks the code blocks into "tokens"
    expect(screen.getByText("console")).toBeInTheDocument();
    expect(screen.getByText("log")).toBeInTheDocument();
    expect(screen.getByText("'Hello'")).toBeInTheDocument();
  });

  describe("copy to clipboard", () => {
    const toastInfoSpy = vi.spyOn(toast, "info");
    const toastErrorSpy = vi.spyOn(toast, "error");

    it("should copy any message to clipboard", async () => {
      const user = userEvent.setup();
      render(
        <ChatMessage
          message={{
            sender: "user",
            content: "Hello",
            imageUrls: [],
            timestamp: new Date().toISOString(),
          }}
          isLastMessage={false}
        />,
      );

      const message = screen.getByTestId("article");
      let copyButton = within(message).queryByTestId("copy-button");
      expect(copyButton).not.toBeInTheDocument();

      // I am using `fireEvent` here because `userEvent.hover()` seems to interfere with the
      // `userEvent.click()` call later on
      fireEvent.mouseEnter(message);

      copyButton = within(message).getByTestId("copy-button");
      await user.click(copyButton);

      expect(navigator.clipboard.readText()).resolves.toBe("Hello");
      expect(toastInfoSpy).toHaveBeenCalled();
    });

    it("should show an error message when the message cannot be copied", async () => {
      const user = userEvent.setup();
      render(
        <ChatMessage
          message={{
            sender: "user",
            content: "Hello",
            imageUrls: [],
            timestamp: new Date().toISOString(),
          }}
          isLastMessage={false}
        />,
      );

      const message = screen.getByTestId("article");
      fireEvent.mouseEnter(message);

      const copyButton = within(message).getByTestId("copy-button");
      const clipboardSpy = vi
        .spyOn(navigator.clipboard, "writeText")
        .mockRejectedValue(new Error("Failed to copy"));

      await user.click(copyButton);

      expect(clipboardSpy).toHaveBeenCalled();
      expect(toastErrorSpy).toHaveBeenCalled();
    });
  });

  describe("confirmation buttons", () => {
    const expectButtonsNotToBeRendered = () => {
      expect(
        screen.queryByTestId("action-confirm-button"),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByTestId("action-reject-button"),
      ).not.toBeInTheDocument();
    };

    it("should display confirmation buttons for the last assistant message", () => {
      // it should not render buttons if the message is not the last one
      const { rerender } = render(
        <ChatMessage
          message={{
            sender: "assistant",
            content: "Are you sure?",
            imageUrls: [],
            timestamp: new Date().toISOString(),
          }}
          isLastMessage={false}
          awaitingUserConfirmation
        />,
      );
      expectButtonsNotToBeRendered();

      // it should not render buttons if the message is not from the assistant
      rerender(
        <ChatMessage
          message={{
            sender: "user",
            content: "Yes",
            imageUrls: [],
            timestamp: new Date().toISOString(),
          }}
          isLastMessage
          awaitingUserConfirmation
        />,
      );
      expectButtonsNotToBeRendered();

      // it should not render buttons if the message is not awaiting user confirmation
      rerender(
        <ChatMessage
          message={{
            sender: "assistant",
            content: "Are you sure?",
            imageUrls: [],
            timestamp: new Date().toISOString(),
          }}
          isLastMessage
          awaitingUserConfirmation={false}
        />,
      );
      expectButtonsNotToBeRendered();

      // it should render buttons if all conditions are met
      rerender(
        <ChatMessage
          message={{
            sender: "assistant",
            content: "Are you sure?",
            imageUrls: [],
            timestamp: new Date().toISOString(),
          }}
          isLastMessage
          awaitingUserConfirmation
        />,
      );

      const confirmButton = screen.getByTestId("action-confirm-button");
      const rejectButton = screen.getByTestId("action-reject-button");

      expect(confirmButton).toBeInTheDocument();
      expect(rejectButton).toBeInTheDocument();
    });
  });
});
