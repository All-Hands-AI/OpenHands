import { render, screen } from "@testing-library/react";
import { it, describe, expect, vi, beforeAll, afterAll } from "vitest";
import userEvent from "@testing-library/user-event";
import { AuthModal } from "#/components/features/waitlist/auth-modal";
import * as CaptureConsent from "#/utils/handle-capture-consent";
import * as AuthHook from "#/context/auth-context";

describe("AuthModal", () => {
  beforeAll(() => {
    vi.stubGlobal("location", { href: "" });
    vi.spyOn(AuthHook, "useAuth").mockReturnValue({
      providersAreSet: false,
      setProvidersAreSet: vi.fn(),
      providerTokensSet: [],
      setProviderTokensSet: vi.fn()
    });
  });

  afterAll(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("should render a tos checkbox that is unchecked by default", () => {
    render(<AuthModal githubAuthUrl={null} appMode="saas" />);
    const checkbox = screen.getByRole("checkbox");

    expect(checkbox).not.toBeChecked();
  });

  it("should only enable the identity provider buttons if the tos checkbox is checked", async () => {
    const user = userEvent.setup();
    render(<AuthModal githubAuthUrl={null} appMode="saas" />);

    const checkbox = screen.getByRole("checkbox");
    const githubButton = screen.getByRole("button", { name: "GITHUB$CONNECT_TO_GITHUB" });
    const gitlabButton = screen.getByRole("button", { name: "GITLAB$CONNECT_TO_GITLAB" });

    expect(githubButton).toBeDisabled();
    expect(gitlabButton).toBeDisabled();

    await user.click(checkbox);

    expect(githubButton).not.toBeDisabled();
    expect(gitlabButton).not.toBeDisabled();
  });

  it("should set user analytics consent to true when the user checks the tos checkbox", async () => {
    const handleCaptureConsentSpy = vi.spyOn(
      CaptureConsent,
      "handleCaptureConsent",
    );

    const user = userEvent.setup();
    render(<AuthModal githubAuthUrl="mock-url" appMode="saas" />);

    const checkbox = screen.getByRole("checkbox");
    await user.click(checkbox);

    const button = screen.getByRole("button", { name: "GITHUB$CONNECT_TO_GITHUB" });
    await user.click(button);

    expect(handleCaptureConsentSpy).toHaveBeenCalledWith(true);
  });
});
