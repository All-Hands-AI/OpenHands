import { render, screen } from "@testing-library/react";
import { it, describe, expect, vi, beforeAll, afterAll } from "vitest";
import userEvent from "@testing-library/user-event";
import { WaitlistModal } from "#/components/features/waitlist/waitlist-modal";
import * as CaptureConsent from "#/utils/handle-capture-consent";

describe("WaitlistModal", () => {
  beforeAll(() => {
    vi.stubGlobal("location", { href: "" });
  });

  afterAll(() => {
    vi.unstubAllGlobals();
  });

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

  it("should set user analytics consent to true when the user checks the tos checkbox", async () => {
    const handleCaptureConsentSpy = vi.spyOn(
      CaptureConsent,
      "handleCaptureConsent",
    );

    const user = userEvent.setup();
    render(<WaitlistModal ghToken={null} githubAuthUrl="mock-url" />);

    const checkbox = screen.getByRole("checkbox");
    await user.click(checkbox);

    const button = screen.getByRole("button", { name: "Connect to GitHub" });
    await user.click(button);

    expect(handleCaptureConsentSpy).toHaveBeenCalledWith(true);
  });
});
