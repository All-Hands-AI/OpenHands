import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { GitRepositorySelector } from "#/components/features/git/git-repo-selector";
import OpenHands from "#/api/open-hands";
import { Provider } from "#/types/settings";

describe("GitRepositorySelector", () => {
  const onInputChangeMock = vi.fn();
  const onSelectMock = vi.fn();

  it("should render the search input", () => {
    renderWithProviders(
      <GitRepositorySelector
        onInputChange={onInputChangeMock}
        onSelect={onSelectMock}
        publicRepositories={[]}
        userRepositories={[]}
      />,
    );

    expect(
      screen.getByPlaceholderText("LANDING$SELECT_GIT_REPO"),
    ).toBeInTheDocument();
  });

  it("should show the GitHub login button in OSS mode", () => {
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    getConfigSpy.mockResolvedValue({
      APP_MODE: "oss",
      APP_SLUG: "openhands",
      GITHUB_CLIENT_ID: "test-client-id",
      POSTHOG_CLIENT_KEY: "test-posthog-key",
      FEATURE_FLAGS: {
        ENABLE_BILLING: false,
        HIDE_LLM_SETTINGS: false,
      },
    });

    renderWithProviders(
      <GitRepositorySelector
        onInputChange={onInputChangeMock}
        onSelect={onSelectMock}
        publicRepositories={[]}
        userRepositories={[]}
      />,
    );

    expect(screen.getByTestId("github-repo-selector")).toBeInTheDocument();
  });

  it("should show the search results", () => {
    const mockSearchedRepos = [
      {
        id: 1,
        full_name: "test/repo1",
        git_provider: "github" as Provider,
        stargazers_count: 100,
        is_public: true,
        pushed_at: "2023-01-01T00:00:00Z",
      },
      {
        id: 2,
        full_name: "test/repo2",
        git_provider: "github" as Provider,
        stargazers_count: 200,
        is_public: true,
        pushed_at: "2023-01-02T00:00:00Z",
      },
    ];

    const searchPublicRepositoriesSpy = vi.spyOn(
      OpenHands,
      "searchGitRepositories",
    );
    searchPublicRepositoriesSpy.mockResolvedValue(mockSearchedRepos);

    renderWithProviders(
      <GitRepositorySelector
        onInputChange={onInputChangeMock}
        onSelect={onSelectMock}
        publicRepositories={[]}
        userRepositories={[]}
      />,
    );

    expect(screen.getByTestId("github-repo-selector")).toBeInTheDocument();
  });
});
