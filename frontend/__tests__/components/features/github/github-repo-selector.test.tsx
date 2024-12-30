import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { GitHubRepositorySelector } from "#/components/features/github/github-repo-selector";
import { useConfig } from "#/hooks/query/use-config";
import { useSearchRepositories } from "#/hooks/query/use-search-repositories";

vi.mock("#/hooks/query/use-config", () => ({
  useConfig: vi.fn(),
}));

vi.mock("#/hooks/query/use-search-repositories", () => ({
  useSearchRepositories: vi.fn(),
}));

vi.mock("react-redux", () => ({
  useDispatch: () => vi.fn(),
}));

vi.mock("posthog-js", () => ({
  default: {
    capture: vi.fn(),
  },
}));

vi.mock("#/context/settings-context", () => ({
  useSettings: () => ({
    settings: {},
    setSettings: vi.fn(),
  }),
}));

describe("GitHubRepositorySelector", () => {
  const mockConfig = {
    APP_MODE: "saas",
    APP_SLUG: "test-app",
  };

  const mockRepositories = [
    { id: 1, full_name: "user/repo1" },
    { id: 2, full_name: "user/repo2" },
  ];

  const mockSearchedRepos = [
    { id: 3, full_name: "other/repo3", stargazers_count: 100 },
    { id: 4, full_name: "other/repo4", stargazers_count: 200 },
  ];

  beforeEach(() => {
    vi.mocked(useConfig).mockReturnValue({ data: mockConfig });
    vi.mocked(useSearchRepositories).mockReturnValue({ data: [] });
  });

  it("should render the repository selector", () => {
    render(
      <GitHubRepositorySelector onSelect={vi.fn()} repositories={mockRepositories} />,
    );

    expect(screen.getByLabelText("GitHub Repository")).toBeInTheDocument();
  });

  it("should show 'Add more repositories...' option in saas mode", async () => {
    const user = userEvent.setup();
    render(
      <GitHubRepositorySelector onSelect={vi.fn()} repositories={mockRepositories} />,
    );

    const input = screen.getByRole("combobox");
    await user.click(input);

    expect(screen.getByText("Add more repositories...")).toBeInTheDocument();
  });

  it("should not show 'Add more repositories...' option in non-saas mode", async () => {
    const user = userEvent.setup();
    vi.mocked(useConfig).mockReturnValue({
      data: { ...mockConfig, APP_MODE: "oss" },
    });

    render(
      <GitHubRepositorySelector onSelect={vi.fn()} repositories={mockRepositories} />,
    );

    const input = screen.getByRole("combobox");
    await user.click(input);

    expect(
      screen.queryByText("Add more repositories..."),
    ).not.toBeInTheDocument();
  });

  it("should show search results with star counts", async () => {
    const user = userEvent.setup();
    vi.mocked(useSearchRepositories).mockReturnValue({ data: mockSearchedRepos });

    render(
      <GitHubRepositorySelector onSelect={vi.fn()} repositories={mockRepositories} />,
    );

    const input = screen.getByRole("combobox");
    await user.click(input);

    expect(screen.getByText("other/repo3")).toBeInTheDocument();
    expect(screen.getByText("(100⭐)")).toBeInTheDocument();
    expect(screen.getByText("other/repo4")).toBeInTheDocument();
    expect(screen.getByText("(200⭐)")).toBeInTheDocument();
  });

  it("should open installation page when clicking 'Add more repositories...'", async () => {
    const user = userEvent.setup();
    const windowSpy = vi.spyOn(window, "open");

    render(
      <GitHubRepositorySelector onSelect={vi.fn()} repositories={mockRepositories} />,
    );

    const input = screen.getByRole("combobox");
    await user.click(input);

    const addMoreOption = screen.getByText("Add more repositories...");
    await user.click(addMoreOption);

    expect(windowSpy).toHaveBeenCalledWith(
      "https://github.com/apps/test-app/installations/new",
      "_blank",
    );
  });
});
