import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { GitHubRepositorySelector } from "#/components/features/github/github-repo-selector";
import OpenHands from "#/api/open-hands";
import * as GitHubAPI from "#/api/github";

describe("GitHubRepositorySelector", () => {
  const onInputChangeMock = vi.fn();
  const onSelectMock = vi.fn();

  it("should render the search input", () => {
    renderWithProviders(
      <GitHubRepositorySelector
        onInputChange={onInputChangeMock}
        onSelect={onSelectMock}
        publicRepositories={[]}
        userRepositories={[]}
      />,
    );

    expect(
      screen.getByPlaceholderText("Select a GitHub project"),
    ).toBeInTheDocument();
  });

  it("should show the GitHub login button in OSS mode", () => {
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    getConfigSpy.mockResolvedValue({
      APP_MODE: "oss",
      APP_SLUG: "openhands",
      GITHUB_CLIENT_ID: "test-client-id",
      POSTHOG_CLIENT_KEY: "test-posthog-key",
    });

    renderWithProviders(
      <GitHubRepositorySelector
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
        stargazers_count: 100,
      },
      {
        id: 2,
        full_name: "test/repo2",
        stargazers_count: 200,
      },
    ];

    const searchPublicRepositoriesSpy = vi.spyOn(
      GitHubAPI,
      "searchPublicRepositories",
    );
    searchPublicRepositoriesSpy.mockResolvedValue(mockSearchedRepos);

    renderWithProviders(
      <GitHubRepositorySelector
        onInputChange={onInputChangeMock}
        onSelect={onSelectMock}
        publicRepositories={[]}
        userRepositories={[]}
      />,
    );

    expect(screen.getByTestId("github-repo-selector")).toBeInTheDocument();
  });
});
