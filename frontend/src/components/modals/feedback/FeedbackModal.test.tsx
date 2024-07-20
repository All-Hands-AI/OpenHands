import { render, screen, within } from "@testing-library/react";
import { Mock, describe } from "vitest";
import React from "react";
import userEvent from "@testing-library/user-event";
import toast from "react-hot-toast";
import FeedbackModal from "./FeedbackModal";
import { sendFeedback } from "#/services/feedbackService";

describe("FeedbackModal", () => {
  Storage.prototype.setItem = vi.fn();
  Storage.prototype.getItem = vi.fn();

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

  afterEach(() => {
    vi.clearAllMocks();
  });

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
    const permissionsGroup = screen.getByTestId("permissions-group");
    const publicOption = within(permissionsGroup).getByRole("radio", {
      name: "FEEDBACK$PUBLIC_LABEL",
    });
    expect(publicOption).not.toBeChecked();
    await user.click(publicOption);
    expect(publicOption).toBeChecked();

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

  it("should store the users email in local state for later use", async () => {
    const email = "example@example.com";

    const user = userEvent.setup();
    const { rerender } = render(
      <FeedbackModal
        polarity="negative"
        isOpen
        onOpenChange={vi.fn}
        onSendFeedback={vi.fn}
      />,
    );

    expect(localStorage.getItem).toHaveBeenCalledWith("feedback-email");
    const emailInput = screen.getByTestId("email-input");
    expect(emailInput).toHaveValue("");

    await user.type(emailInput, email);
    expect(emailInput).toHaveValue(email);

    const submitButton = screen.getByRole("button", {
      name: "FEEDBACK$SHARE_LABEL",
    });
    await user.click(submitButton);

    expect(localStorage.setItem).toHaveBeenCalledWith("feedback-email", email);

    rerender(
      <FeedbackModal
        polarity="positive"
        isOpen
        onOpenChange={vi.fn}
        onSendFeedback={vi.fn}
      />,
    );

    const emailInputAfterClose = screen.getByTestId("email-input");
    expect(emailInputAfterClose).toHaveValue(email);
  });

  // TODO: figure out how to properly mock toast
  it.skip("should display a success toast when the feedback is shared successfully", async () => {
    (sendFeedback as Mock).mockResolvedValue({
      statusCode: 200,
      body: {
        message: "Feedback shared",
        feedback_id: "some-id",
        password: "some-password",
      },
    });

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

    await user.click(submitButton);

    expect(toast).toHaveBeenCalled();
  });
});
