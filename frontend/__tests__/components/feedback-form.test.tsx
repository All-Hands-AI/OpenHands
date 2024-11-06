import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { FeedbackForm } from "#/components/feedback-form";

describe("FeedbackForm", () => {
  const user = userEvent.setup();
  const onCloseMock = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render correctly", () => {
    render(<FeedbackForm polarity="positive" onClose={onCloseMock} />);

    screen.getByLabelText("Email");
    screen.getByLabelText("Private");
    screen.getByLabelText("Public");

    screen.getByRole("button", { name: "Submit" });
    screen.getByRole("button", { name: "Cancel" });
  });

  it("should switch between private and public permissions", async () => {
    render(<FeedbackForm polarity="positive" onClose={onCloseMock} />);
    const privateRadio = screen.getByLabelText("Private");
    const publicRadio = screen.getByLabelText("Public");

    expect(privateRadio).toBeChecked(); // private is the default value
    expect(publicRadio).not.toBeChecked();

    await user.click(publicRadio);
    expect(publicRadio).toBeChecked();
    expect(privateRadio).not.toBeChecked();

    await user.click(privateRadio);
    expect(privateRadio).toBeChecked();
    expect(publicRadio).not.toBeChecked();
  });

  it("should call onClose when the close button is clicked", async () => {
    render(<FeedbackForm polarity="positive" onClose={onCloseMock} />);
    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onCloseMock).toHaveBeenCalled();
  });

});
