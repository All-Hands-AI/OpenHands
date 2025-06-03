import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import { EventMessage } from "#/components/features/chat/event-message";
import { UserMessageAction } from "#/types/core/actions";

const userMessage: UserMessageAction = {
  id: 1,
  action: "message",
  message: "Hello, World!",
  source: "user",
  args: { content: "Hello, World!", image_urls: [] },
  timestamp: new Date().toISOString(),
};

function EventMessageWithPortalExit() {
  return (
    <>
      <EventMessage
        event={userMessage}
        hasObservationPair={false}
        isAwaitingUserConfirmation={false}
        isLastMessage={false}
        assistantMessageActionButton={null}
      />

      <div id="modal-portal-exit" data-testid="modal-container" />
    </>
  );
}

describe("EventMessage", () => {
  it("should render an event message", () => {
    render(
      <EventMessage
        event={userMessage}
        hasObservationPair={false}
        isAwaitingUserConfirmation={false}
        isLastMessage={false}
        assistantMessageActionButton={null}
      />,
    );

    expect(screen.getByText("Hello, World!")).toBeInTheDocument();
  });

  it("should render the launch microagent modal on click", async () => {
    render(<EventMessageWithPortalExit />);

    const message = screen.getByText("Hello, World!");
    await userEvent.hover(message);

    const launchMicroagentButton = screen.getByTestId(
      "launch-microagent-button",
    );
    expect(launchMicroagentButton).toBeInTheDocument();

    await userEvent.click(launchMicroagentButton);

    const portalContainer = screen.getByTestId("modal-container");
    const modalElement = within(portalContainer).getByTestId(
      "launch-microagent-modal",
    );

    expect(modalElement).toBeInTheDocument();
  });

  it("should hide the modal when clicking cancel", async () => {
    render(<EventMessageWithPortalExit />);

    const message = screen.getByText("Hello, World!");
    await userEvent.hover(message);

    const launchMicroagentButton = screen.getByTestId(
      "launch-microagent-button",
    );
    expect(launchMicroagentButton).toBeInTheDocument();

    await userEvent.click(launchMicroagentButton);

    const portalContainer = screen.getByTestId("modal-container");
    const modalElement = within(portalContainer).getByTestId(
      "launch-microagent-modal",
    );

    expect(modalElement).toBeInTheDocument();

    const cancelButton = within(modalElement).getByRole("button", {
      name: "Cancel",
    });
    await userEvent.click(cancelButton);

    expect(modalElement).not.toBeInTheDocument();
  });
});
