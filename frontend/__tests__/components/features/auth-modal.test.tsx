import { render, screen } from "@testing-library/react";
import { it, describe, expect, vi, beforeEach, afterEach } from "vitest";
import userEvent from "@testing-library/user-event";
import { AuthModal } from "#/components/features/waitlist/auth-modal";

// Mock the useAuthUrl hook
vi.mock("#/hooks/use-auth-url", () => ({
  useAuthUrl: (params: any) => {
    if (params?.identityProvider === "gitlab") {
      return "https://gitlab.com/oauth/authorize";
    } else if (params?.identityProvider === "azure_devops") {
      return "https://dev.azure.com/oauth/authorize";
    }
    return null;
  }
}));

describe("AuthModal", () => {
  beforeEach(() => {
    vi.stubGlobal("location", { href: "" });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.resetAllMocks();
  });

  it("should render the GitHub, GitLab, and Azure DevOps buttons", () => {
    render(<AuthModal githubAuthUrl="mock-url" appMode="saas" />);

    const githubButton = screen.getByRole("button", {
      name: "GITHUB$CONNECT_TO_GITHUB",
    });
    const gitlabButton = screen.getByRole("button", {
      name: "GITLAB$CONNECT_TO_GITLAB",
    });
    const azureDevOpsButton = screen.getByRole("button", {
      name: "AZURE_DEVOPS$CONNECT_TO_AZURE_DEVOPS",
    });

    expect(githubButton).toBeInTheDocument();
    expect(gitlabButton).toBeInTheDocument();
    expect(azureDevOpsButton).toBeInTheDocument();
  });

  it("should redirect to GitHub auth URL when GitHub button is clicked", async () => {
    const user = userEvent.setup();
    const mockUrl = "https://github.com/login/oauth/authorize";
    render(<AuthModal githubAuthUrl={mockUrl} appMode="saas" />);

    const githubButton = screen.getByRole("button", {
      name: "GITHUB$CONNECT_TO_GITHUB",
    });
    await user.click(githubButton);

    expect(window.location.href).toBe(mockUrl);
  });

  it("should redirect to Azure DevOps auth URL when Azure DevOps button is clicked", async () => {
    const user = userEvent.setup();
    const mockUrl = "https://dev.azure.com/oauth/authorize";
    render(<AuthModal githubAuthUrl="mock-github-url" appMode="saas" />);

    const azureDevOpsButton = screen.getByRole("button", {
      name: "AZURE_DEVOPS$CONNECT_TO_AZURE_DEVOPS",
    });
    await user.click(azureDevOpsButton);

    expect(window.location.href).toBe(mockUrl);
  });
});
