import { render, screen } from "@testing-library/react";
import { it, describe, expect } from "vitest";
import userEvent from "@testing-library/user-event";
import { WaitlistModal } from "#/components/features/waitlist/waitlist-modal";

describe("WaitlistModal", () => {
  it("should render a tos checkbox that is unchecked by default", () => {
    render(<WaitlistModal ghToken={null} githubAuthUrl={null} />);
    const checkbox = screen.getByRole("checkbox");

    expect(checkbox).not.toBeChecked();
  });

  it("should only enable the GitHub button if the tos checkbox is checked", async () => {
    const user = userEvent.setup();
    render(<WaitlistModal ghToken={null} githubAuthUrl={null} />);
    const checkbox = screen.getByRole("checkbox");
    const button = screen.getByRole("button", { name: "Connect to GitHub" });

    expect(button).toBeDisabled();

    await user.click(checkbox);

    expect(button).not.toBeDisabled();
  });
});
