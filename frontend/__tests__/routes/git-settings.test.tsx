import { render, screen, waitFor } from "@testing-library/react";
import { createRoutesStub } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import GitSettingsScreen from "#/routes/git-settings";
import OpenHands from "#/api/open-hands";
import { MOCK_DEFAULT_USER_SETTINGS } from "#/mocks/handlers";
import { AuthProvider } from "#/context/auth-context";
import { GetConfigResponse } from "#/api/open-hands.types";

const VALID_OSS_CONFIG: GetConfigResponse = {
  APP_MODE: "oss",
  GITHUB_CLIENT_ID: "123",
  POSTHOG_CLIENT_KEY: "456",
  FEATURE_FLAGS: {
    ENABLE_BILLING: false,
    HIDE_LLM_SETTINGS: false,
  },
};

const VALID_SAAS_CONFIG: GetConfigResponse = {
  APP_MODE: "saas",
  GITHUB_CLIENT_ID: "123",
  POSTHOG_CLIENT_KEY: "456",
  FEATURE_FLAGS: {
    ENABLE_BILLING: false,
    HIDE_LLM_SETTINGS: false,
  },
};

const queryClient = new QueryClient();

const GitSettingsRouterStub = createRoutesStub([
  {
    Component: GitSettingsScreen,
    path: "/settings/github",
  },
]);

const renderGitSettingsScreen = () => {
  const { rerender, ...rest } = render(
    <GitSettingsRouterStub initialEntries={["/settings/github"]} />,
    {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          <AuthProvider>{children}</AuthProvider>
        </QueryClientProvider>
      ),
    },
  );

  const rerenderGitSettingsScreen = () =>
    rerender(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <GitSettingsRouterStub initialEntries={["/settings/github"]} />
        </AuthProvider>
      </QueryClientProvider>,
    );

  return {
    ...rest,
    rerender: rerenderGitSettingsScreen,
  };
};

beforeEach(() => {
  // Since we don't recreate the query client on every test, we need to
  // reset the query client before each test to avoid state leaks
  // between tests.
  queryClient.invalidateQueries();
});

describe("Content", () => {
  it("should render", async () => {
    renderGitSettingsScreen();
    await screen.findByTestId("git-settings-screen");
  });

  it("should render the inputs if OSS mode", async () => {
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    getConfigSpy.mockResolvedValue(VALID_OSS_CONFIG);

    const { rerender } = renderGitSettingsScreen();

    await screen.findByTestId("github-token-input");
    await screen.findByTestId("github-token-help-anchor");

    await screen.findByTestId("gitlab-token-input");
    await screen.findByTestId("gitlab-token-help-anchor");

    getConfigSpy.mockResolvedValue(VALID_SAAS_CONFIG);
    queryClient.invalidateQueries();
    rerender();

    await waitFor(() => {
      expect(
        screen.queryByTestId("github-token-input"),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByTestId("github-token-help-anchor"),
      ).not.toBeInTheDocument();

      expect(
        screen.queryByTestId("gitlab-token-input"),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByTestId("gitlab-token-help-anchor"),
      ).not.toBeInTheDocument();
    });
  });

  it("should set '<hidden>' placeholder if the GitHub token is set", async () => {
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");

    getConfigSpy.mockResolvedValue(VALID_OSS_CONFIG);
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      provider_tokens_set: {
        github: false,
        gitlab: false,
      },
    });

    const { rerender } = renderGitSettingsScreen();

    await waitFor(() => {
      const githubInput = screen.getByTestId("github-token-input");
      expect(githubInput).toHaveProperty("placeholder", "");

      const gitlabInput = screen.getByTestId("gitlab-token-input");
      expect(gitlabInput).toHaveProperty("placeholder", "");
    });

    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      provider_tokens_set: {
        github: true,
        gitlab: true,
      },
    });
    queryClient.invalidateQueries();

    rerender();

    await waitFor(() => {
      const githubInput = screen.getByTestId("github-token-input");
      expect(githubInput).toHaveProperty("placeholder", "<hidden>");

      const gitlabInput = screen.getByTestId("gitlab-token-input");
      expect(gitlabInput).toHaveProperty("placeholder", "<hidden>");
    });

    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      provider_tokens_set: {
        github: false,
        gitlab: true,
      },
    });
    queryClient.invalidateQueries();

    rerender();

    await waitFor(() => {
      const githubInput = screen.getByTestId("github-token-input");
      expect(githubInput).toHaveProperty("placeholder", "");

      const gitlabInput = screen.getByTestId("gitlab-token-input");
      expect(gitlabInput).toHaveProperty("placeholder", "<hidden>");
    });
  });

  it("should render the 'Configure GitHub Repositories' button if SaaS mode and app slug exists", async () => {
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    getConfigSpy.mockResolvedValue(VALID_OSS_CONFIG);

    const { rerender } = renderGitSettingsScreen();

    let button = screen.queryByTestId("configure-github-repositories-button");
    expect(button).not.toBeInTheDocument();

    getConfigSpy.mockResolvedValue(VALID_SAAS_CONFIG);
    queryClient.invalidateQueries();
    rerender();

    await waitFor(() => {
      // wait until queries are resolved
      expect(queryClient.isFetching()).toBe(0);
      button = screen.queryByTestId("configure-github-repositories-button");
      expect(button).not.toBeInTheDocument();
    });

    getConfigSpy.mockResolvedValue({
      ...VALID_SAAS_CONFIG,
      APP_SLUG: "test-slug",
    });
    queryClient.invalidateQueries();
    rerender();

    await waitFor(() => {
      button = screen.getByTestId("configure-github-repositories-button");
      expect(button).toBeInTheDocument();
    });
  });
});

describe("Form submission", () => {
  it("should save the GitHub token", async () => {
    const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    getConfigSpy.mockResolvedValue(VALID_OSS_CONFIG);

    renderGitSettingsScreen();

    const githubInput = await screen.findByTestId("github-token-input");
    const submit = await screen.findByTestId("submit-button");

    await userEvent.type(githubInput, "test-token");
    await userEvent.click(submit);

    expect(saveSettingsSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        provider_tokens: {
          github: "test-token",
          gitlab: "",
        },
      }),
    );

    const gitlabInput = await screen.findByTestId("gitlab-token-input");
    await userEvent.type(gitlabInput, "test-token");
    await userEvent.click(submit);

    expect(saveSettingsSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        provider_tokens: {
          github: "",
          gitlab: "test-token",
        },
      }),
    );
  });

  it("should disable the button if there is no input", async () => {
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    getConfigSpy.mockResolvedValue(VALID_OSS_CONFIG);

    renderGitSettingsScreen();

    const submit = await screen.findByTestId("submit-button");
    expect(submit).toBeDisabled();

    const githubInput = await screen.findByTestId("github-token-input");
    await userEvent.type(githubInput, "test-token");

    expect(submit).not.toBeDisabled();

    await userEvent.clear(githubInput);
    expect(submit).toBeDisabled();

    const gitlabInput = await screen.findByTestId("gitlab-token-input");
    await userEvent.type(gitlabInput, "test-token");

    expect(submit).not.toBeDisabled();

    await userEvent.clear(gitlabInput);
    expect(submit).toBeDisabled();
  });
});
