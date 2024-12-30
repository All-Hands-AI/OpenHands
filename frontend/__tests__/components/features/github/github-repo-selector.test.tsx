import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { useConfig } from "#/hooks/query/use-config";
import { useSearchRepositories } from "#/hooks/query/use-search-repositories";
import { GitHubRepositorySelector } from "#/components/features/github/github-repo-selector";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import initialQueryReducer from "#/state/initial-query-slice";

vi.mock("#/hooks/query/use-config");
vi.mock("#/hooks/query/use-search-repositories");

const store = configureStore({
  reducer: {
    initialQuery: initialQueryReducer,
  },
});

describe("GitHubRepositorySelector", () => {
  const user = userEvent.setup();
  const onSelectMock = vi.fn();

  const mockConfig = {
    APP_MODE: "saas" as const,
    APP_SLUG: "openhands",
    GITHUB_CLIENT_ID: "test-client-id",
    POSTHOG_CLIENT_KEY: "test-posthog-key",
  };

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

  const mockQueryResult = {
    data: mockConfig,
    error: null,
    isError: false as const,
    isPending: false as const,
    isLoading: false as const,
    isFetching: false as const,
    isSuccess: true as const,
    status: "success" as const,
    refetch: vi.fn(),
    isLoadingError: false as const,
    isRefetchError: false as const,
    dataUpdatedAt: Date.now(),
    errorUpdatedAt: Date.now(),
    failureCount: 0,
    failureReason: null,
    errorUpdateCount: 0,
    isInitialLoading: false as const,
    isPlaceholderData: false as const,
    isPreviousData: false as const,
    isRefetching: false as const,
    isStale: false as const,
    remove: vi.fn(),
    isFetched: true as const,
    isFetchedAfterMount: true as const,
    isPaused: false as const,
    fetchStatus: "idle" as const,
    promise: Promise.resolve(mockConfig),
  };

  const mockSearchResult = {
    ...mockQueryResult,
    data: [],
    promise: Promise.resolve([]),
  };

  it("should render the search input", () => {
    vi.mocked(useConfig).mockReturnValue(mockQueryResult);
    vi.mocked(useSearchRepositories).mockReturnValue(mockSearchResult);

    render(
      <Provider store={store}>
        <GitHubRepositorySelector onSelect={onSelectMock} repositories={[]} />
      </Provider>,
    );

    expect(screen.getByPlaceholderText("Select a GitHub project")).toBeInTheDocument();
  });

  it("should show the GitHub login button in OSS mode", () => {
    const ossConfig = { ...mockConfig, APP_MODE: "oss" as const };
    vi.mocked(useConfig).mockReturnValue({
      ...mockQueryResult,
      data: ossConfig,
      promise: Promise.resolve(ossConfig),
    });
    vi.mocked(useSearchRepositories).mockReturnValue(mockSearchResult);

    render(
      <Provider store={store}>
        <GitHubRepositorySelector onSelect={onSelectMock} repositories={[]} />
      </Provider>,
    );

    expect(screen.getByTestId("github-repo-selector")).toBeInTheDocument();
  });

  it("should show the search results", () => {
    vi.mocked(useConfig).mockReturnValue(mockQueryResult);
    vi.mocked(useSearchRepositories).mockReturnValue({
      ...mockQueryResult,
      data: mockSearchedRepos,
      promise: Promise.resolve(mockSearchedRepos),
    });

    render(
      <Provider store={store}>
        <GitHubRepositorySelector onSelect={onSelectMock} repositories={[]} />
      </Provider>,
    );

    expect(screen.getByTestId("github-repo-selector")).toBeInTheDocument();
  });
});
