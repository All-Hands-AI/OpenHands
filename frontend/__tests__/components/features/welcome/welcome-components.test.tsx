import React from "react";
import { render, screen } from "@testing-library/react";
import { vi, describe, it, expect } from "vitest";
import { WelcomeHeader } from "#/components/features/welcome/welcome-header";
import { ConnectToRepo } from "#/components/features/welcome/connect-to-repo";
import { SuggestedTasks } from "#/components/features/welcome/suggested-tasks";
import { LaunchFromScratchButton } from "#/components/features/welcome/launch-from-scratch-button";

// Mock the i18n
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

// Mock the GitHub user hook
vi.mock("#/hooks/query/use-github-user", () => ({
  useGitHubUser: () => ({
    data: null,
    isLoading: false,
    error: null,
  }),
}));

describe("Welcome Components", () => {
  describe("WelcomeHeader", () => {
    it("renders correctly", () => {
      render(<WelcomeHeader />);
      // Just check that the component renders without errors
      expect(screen.getByRole("heading")).toBeInTheDocument();
    });
  });

  describe("ConnectToRepo", () => {
    it("renders correctly with children", () => {
      render(
        <ConnectToRepo>
          <div data-testid="test-child">Test Child</div>
        </ConnectToRepo>
      );
      expect(screen.getByText("Connect to a Repo")).toBeInTheDocument();
      expect(screen.getByTestId("test-child")).toBeInTheDocument();
      expect(screen.getByText("Launch")).toBeInTheDocument();
      expect(screen.getByText("Add GitHub repos")).toBeInTheDocument();
      expect(screen.getByText("Add GitLab repos")).toBeInTheDocument();
    });
  });

  describe("SuggestedTasks", () => {
    it("renders correctly", () => {
      render(<SuggestedTasks />);
      expect(screen.getByText("Suggested Tasks")).toBeInTheDocument();
      // When not logged in, it should show a message to sign in
      expect(screen.getByText("Sign in with GitHub to see suggested tasks")).toBeInTheDocument();
    });
  });

  describe("LaunchFromScratchButton", () => {
    it("renders correctly and calls onClick when clicked", () => {
      const handleClick = vi.fn();
      render(<LaunchFromScratchButton onClick={handleClick} />);
      const button = screen.getByText("Launch From Scratch");
      expect(button).toBeInTheDocument();
      button.click();
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });
});