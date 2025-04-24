import { render, screen } from "@testing-library/react";
import { it, describe, expect, vi, beforeEach, afterEach } from "vitest";
import userEvent from "@testing-library/user-event";
import AcceptTOS from "#/routes/accept-tos";
import * as CaptureConsent from "#/utils/handle-capture-consent";
import { openHands } from "#/api/open-hands-axios";

// Mock the react-router hooks
vi.mock("react-router", () => ({
  useNavigate: () => vi.fn(),
  useSearchParams: () => [
    {
      get: (param: string) => {
        if (param === "redirect_url") {
          return "/dashboard";
        }
        return null;
      },
    },
  ],
}));

// Mock the axios instance
vi.mock("#/api/open-hands-axios", () => ({
  openHands: {
    post: vi.fn(),
  },
}));

describe("AcceptTOS", () => {
  beforeEach(() => {
    vi.stubGlobal("location", { href: "" });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.resetAllMocks();
  });

  it("should render a TOS checkbox that is unchecked by default", () => {
    render(<AcceptTOS />);
    
    const checkbox = screen.getByRole("checkbox");
    const continueButton = screen.getByRole("button", { name: "TOS$CONTINUE" });

    expect(checkbox).not.toBeChecked();
    expect(continueButton).toBeDisabled();
  });

  it("should enable the continue button when the TOS checkbox is checked", async () => {
    const user = userEvent.setup();
    render(<AcceptTOS />);
    
    const checkbox = screen.getByRole("checkbox");
    const continueButton = screen.getByRole("button", { name: "TOS$CONTINUE" });

    expect(continueButton).toBeDisabled();

    await user.click(checkbox);

    expect(continueButton).not.toBeDisabled();
  });

  it("should set user analytics consent to true when the user accepts TOS", async () => {
    const handleCaptureConsentSpy = vi.spyOn(
      CaptureConsent,
      "handleCaptureConsent",
    );

    // Mock the API response
    vi.mocked(openHands.post).mockResolvedValue({
      data: { redirect_url: "/dashboard" },
    });

    const user = userEvent.setup();
    render(<AcceptTOS />);
    
    const checkbox = screen.getByRole("checkbox");
    await user.click(checkbox);

    const continueButton = screen.getByRole("button", { name: "TOS$CONTINUE" });
    await user.click(continueButton);

    expect(handleCaptureConsentSpy).toHaveBeenCalledWith(true);
    expect(openHands.post).toHaveBeenCalledWith("/api/accept_tos", {
      redirect_url: "/dashboard",
    });
  });

  it("should handle external redirect URLs", async () => {
    // Mock the API response with an external URL
    const externalUrl = "https://example.com/callback";
    vi.mocked(openHands.post).mockResolvedValue({
      data: { redirect_url: externalUrl },
    });

    const user = userEvent.setup();
    render(<AcceptTOS />);
    
    const checkbox = screen.getByRole("checkbox");
    await user.click(checkbox);

    const continueButton = screen.getByRole("button", { name: "TOS$CONTINUE" });
    await user.click(continueButton);

    expect(window.location.href).toBe(externalUrl);
  });
});