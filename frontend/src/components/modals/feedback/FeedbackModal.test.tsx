import { render, screen } from "@testing-library/react";
import { describe } from "vitest";
import React from "react";
import userEvent from "@testing-library/user-event";
import FeedbackModal from "./FeedbackModal";
import { sendFeedback } from "#/services/feedbackService";

describe("FeedbackModal", () => {
  vi.mock("#/services/feedbackService", () => ({
    sendFeedback: vi.fn(),
  }));

  vi.mock("#/services/auth", () => ({
    getToken: vi.fn().mockReturnValue("some-token"),
  }));

  // mock Session class
  vi.mock("#/services/session", () => ({
    default: {
      _history: [
        { args: { LLM_API_KEY: "DANGER-key-should-not-be-here" } },
        { content: "Hello" },
      ],
    },
  }));

  it("should render the feedback model when open", () => {
    const { rerender } = render(
      <FeedbackModal
        polarity="positive"
        isOpen={false}
        onOpenChange={vi.fn}
        onSendFeedback={vi.fn}
      />,
    );
    expect(screen.queryByTestId("feedback-modal")).not.toBeInTheDocument();

    rerender(
      <FeedbackModal
        polarity="positive"
        isOpen
        onOpenChange={vi.fn}
        onSendFeedback={vi.fn}
      />,
    );
    expect(screen.getByTestId("feedback-modal")).toBeInTheDocument();
  });

  it("should display an error if the email is invalid when submitting", async () => {
    const user = userEvent.setup();
    render(
      <FeedbackModal
        polarity="positive"
        isOpen
        onOpenChange={vi.fn}
        onSendFeedback={vi.fn}
      />,
    );

    const submitButton = screen.getByRole("button", {
      name: "FEEDBACK$SHARE_LABEL",
    });

    await user.click(submitButton);

    expect(screen.getByTestId("invalid-email-message")).toBeInTheDocument();
    expect(sendFeedback).not.toHaveBeenCalled();
  });

  it("should call sendFeedback with the correct data when the share button is clicked", async () => {
    const user = userEvent.setup();
    render(
      <FeedbackModal
        polarity="negative"
        isOpen
        onOpenChange={vi.fn}
        onSendFeedback={vi.fn}
      />,
    );

    const submitButton = screen.getByRole("button", {
      name: "FEEDBACK$SHARE_LABEL",
    });

    const email = "example@example.com";
    const emailInput = screen.getByTestId("email-input");
    await user.type(emailInput, email);

    // select public
    const permissionsInput = screen.getByTestId("permissions-input");
    await user.click(permissionsInput);
    const publicOption = screen.getByRole("option", { name: "Public" });
    await user.click(publicOption);

    await user.click(submitButton);

    expect(
      screen.queryByTestId("invalid-email-message"),
    ).not.toBeInTheDocument();

    expect(sendFeedback).toHaveBeenCalledWith({
      email,
      permissions: "public",
      feedback: "negative",
      trajectory: [{ args: {} }, { content: "Hello" }], // api key should be removed
      token: "some-token",
      version: "1.0",
    });
  });
});
