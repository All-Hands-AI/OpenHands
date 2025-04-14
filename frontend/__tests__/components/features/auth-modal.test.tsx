import { render, screen } from "@testing-library/react";
import { it, describe, expect, vi, beforeAll, afterAll } from "vitest";
import userEvent from "@testing-library/user-event";
import { AuthModal } from "#/components/features/waitlist/auth-modal";
import * as CaptureConsent from "#/utils/handle-capture-consent";

describe("AuthModal", () => {
  beforeAll(() => {
    vi.stubGlobal("location", { href: "" });
  });

  afterAll(() => {
    vi.unstubAllGlobals();
  });

  it("should render a tos checkbox that is unchecked by default", () => {
    render(<AuthModal githubAuthUrl={null} />);
    const checkbox = screen.getByRole("checkbox");

    expect(checkbox).not.toBeChecked();
  });

  it("should only enable the GitHub button if the tos checkbox is checked", async () => {
    const user = userEvent.setup();
    render(<AuthModal githubAuthUrl={null} />);
    const checkbox = screen.getByRole("checkbox");
    const button = screen.getByRole("button", { name: "GITHUB$CONNECT_TO_GITHUB" });

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
    render(<AuthModal githubAuthUrl="mock-url" />);

    const checkbox = screen.getByRole("checkbox");
    await user.click(checkbox);

    const button = screen.getByRole("button", { name: "GITHUB$CONNECT_TO_GITHUB" });
    await user.click(button);

    expect(handleCaptureConsentSpy).toHaveBeenCalledWith(true);
  });
});
