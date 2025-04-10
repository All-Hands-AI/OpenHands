import { RepoConnector } from "#/components/features/home/repo-connector";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import * as GitService from "#/api/git";
import { GitRepository } from "#/types/git";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { AuthProvider } from "#/context/auth-context";
import OpenHands from "#/api/open-hands";

const renderRepoConnector = () =>
  render(<RepoConnector />, {
    wrapper: ({ children }) => (
      // `initialProvidersAreSet` is required in order for the query hook to trigger
      <AuthProvider initialProvidersAreSet>
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      </AuthProvider>
    ),
  });

const MOCK_RESPOSITORIES: GitRepository[] = [
  { id: 1, full_name: "rbren/polaris", git_provider: "github" },
  { id: 2, full_name: "All-Hands-AI/OpenHands", git_provider: "github" },
];

describe("RepoConnector", () => {
  it("should render the repository connector section", () => {
    renderRepoConnector();
    screen.getByTestId("repo-connector");
  });

  it("should render the available repositories in the dropdown", async () => {
    const retrieveUserGitRepositoriesSpy = vi.spyOn(
      GitService,
      "retrieveUserGitRepositories",
    );
    retrieveUserGitRepositoriesSpy.mockResolvedValue({
      data: MOCK_RESPOSITORIES,
      nextPage: null,
    });

    renderRepoConnector();

    const dropdown = screen.getByTestId("repo-dropdown");
    await userEvent.click(dropdown);

    await waitFor(() => {
      screen.getByText("rbren/polaris");
      screen.getByText("All-Hands-AI/OpenHands");
    });
  });

  it("should only enable the launch button if a repo is selected", async () => {
    const retrieveUserGitRepositoriesSpy = vi.spyOn(
      GitService,
      "retrieveUserGitRepositories",
    );
    retrieveUserGitRepositoriesSpy.mockResolvedValue({
      data: MOCK_RESPOSITORIES,
      nextPage: null,
    });

    renderRepoConnector();

    const launchButton = screen.getByTestId("launch-button");
    expect(launchButton).toBeDisabled();

    const dropdown = screen.getByTestId("repo-dropdown");
    await userEvent.click(dropdown);
    await userEvent.click(screen.getByText("rbren/polaris"));

    expect(launchButton).toBeEnabled();
  });

  it("should render the 'add git(hub|lab) repos' links if oss mode", async () => {
    const getConfiSpy = vi.spyOn(OpenHands, "getConfig");
    // @ts-expect-error - only return the APP_MODE
    getConfiSpy.mockResolvedValue({
      APP_MODE: "oss",
    });

    renderRepoConnector();

    await screen.findByText("Add GitHub repos");
    await screen.findByText("Add GitLab repos");
  });

  it("should not render the 'add git(hub|lab) repos' links if saas mode", async () => {
    const getConfiSpy = vi.spyOn(OpenHands, "getConfig");
    // @ts-expect-error - only return the APP_MODE
    getConfiSpy.mockResolvedValue({
      APP_MODE: "saas",
    });

    renderRepoConnector();

    expect(screen.queryByText("Add GitHub repos")).not.toBeInTheDocument();
    expect(screen.queryByText("Add GitLab repos")).not.toBeInTheDocument();
  });
});
