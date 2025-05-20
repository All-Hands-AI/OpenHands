import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { LaunchMicroagentModal } from "#/components/features/chat/launch-miocroagent-modal";

describe("LaunchMicroagentModal", () => {
  const onCloseMock = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render the launch microagent modal", () => {
    render(<LaunchMicroagentModal onClose={onCloseMock} />);
    expect(screen.getByTestId("launch-microagent-modal")).toBeInTheDocument();
  });

  it("should render the form fields", () => {
    render(<LaunchMicroagentModal onClose={onCloseMock} />);

    // inputs
    screen.getByTestId("description-input");
    screen.getByTestId("name-input");
    screen.getByTestId("target-input");
    screen.getByTestId("trigger-input");

    // action buttons
    screen.getByRole("button", { name: "Launch" });
    screen.getByRole("button", { name: "Cancel" });
  });

  it("should call onClose when pressing the cancel button", async () => {
    render(<LaunchMicroagentModal onClose={onCloseMock} />);

    const cancelButton = screen.getByRole("button", { name: "Cancel" });
    await userEvent.click(cancelButton);
    expect(onCloseMock).toHaveBeenCalled();
  });
});
