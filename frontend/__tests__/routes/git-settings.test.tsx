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
import * as ToastHandlers from "#/utils/custom-toast-handlers";

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

  it("should set '<hidden>' placeholder and indicator if the GitHub token is set", async () => {
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
      expect(
        screen.queryByTestId("gh-set-token-indicator"),
      ).not.toBeInTheDocument();

      const gitlabInput = screen.getByTestId("gitlab-token-input");
      expect(gitlabInput).toHaveProperty("placeholder", "");
      expect(
        screen.queryByTestId("gl-set-token-indicator"),
      ).not.toBeInTheDocument();
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
      expect(
        screen.queryByTestId("gh-set-token-indicator"),
      ).toBeInTheDocument();

      const gitlabInput = screen.getByTestId("gitlab-token-input");
      expect(gitlabInput).toHaveProperty("placeholder", "<hidden>");
      expect(
        screen.queryByTestId("gl-set-token-indicator"),
      ).toBeInTheDocument();
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
      expect(
        screen.queryByTestId("gh-set-token-indicator"),
      ).not.toBeInTheDocument();

      const gitlabInput = screen.getByTestId("gitlab-token-input");
      expect(gitlabInput).toHaveProperty("placeholder", "<hidden>");
      expect(
        screen.queryByTestId("gl-set-token-indicator"),
      ).toBeInTheDocument();
    });
  });

  it("should render the 'Configure GitHub Repositories' button if SaaS mode and app slug exists", async () => {
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    getConfigSpy.mockResolvedValue(VALID_OSS_CONFIG);

    const { rerender } = renderGitSettingsScreen();

    let button = screen.queryByTestId("configure-github-repositories-button");
    expect(button).not.toBeInTheDocument();

    expect(screen.getByTestId("submit-button")).toBeInTheDocument();
    expect(screen.getByTestId("disconnect-tokens-button")).toBeInTheDocument();

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
      expect(screen.queryByTestId("submit-button")).not.toBeInTheDocument();
      expect(
        screen.queryByTestId("disconnect-tokens-button"),
      ).not.toBeInTheDocument();
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

  it("should enable a disconnect tokens button if there is at least one token set", async () => {
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");

    getConfigSpy.mockResolvedValue(VALID_OSS_CONFIG);
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      provider_tokens_set: {
        github: true,
        gitlab: false,
      },
    });

    renderGitSettingsScreen();
    await screen.findByTestId("git-settings-screen");

    let disconnectButton = await screen.findByTestId(
      "disconnect-tokens-button",
    );
    await waitFor(() => expect(disconnectButton).not.toBeDisabled());

    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      provider_tokens_set: {
        github: false,
        gitlab: false,
      },
    });
    queryClient.invalidateQueries();

    disconnectButton = await screen.findByTestId("disconnect-tokens-button");
    await waitFor(() => expect(disconnectButton).toBeDisabled());
  });

  it("should call logout when pressing the disconnect tokens button", async () => {
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    const logoutSpy = vi.spyOn(OpenHands, "logout");
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");

    getConfigSpy.mockResolvedValue(VALID_OSS_CONFIG);
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      provider_tokens_set: {
        github: true,
        gitlab: false,
      },
    });

    renderGitSettingsScreen();

    const disconnectButton = await screen.findByTestId(
      "disconnect-tokens-button",
    );
    await waitFor(() => expect(disconnectButton).not.toBeDisabled());
    await userEvent.click(disconnectButton);

    expect(logoutSpy).toHaveBeenCalled();
  });

  // flaky test
  it.skip("should disable the button when submitting changes", async () => {
    const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    getConfigSpy.mockResolvedValue(VALID_OSS_CONFIG);

    renderGitSettingsScreen();

    const submit = await screen.findByTestId("submit-button");
    expect(submit).toBeDisabled();

    const githubInput = await screen.findByTestId("github-token-input");
    await userEvent.type(githubInput, "test-token");
    expect(submit).not.toBeDisabled();

    // submit the form
    await userEvent.click(submit);
    expect(saveSettingsSpy).toHaveBeenCalled();

    expect(submit).toHaveTextContent("Saving...");
    expect(submit).toBeDisabled();

    await waitFor(() => expect(submit).toHaveTextContent("Save"));
  });

  it("should disable the button after submitting changes", async () => {
    const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    getConfigSpy.mockResolvedValue(VALID_OSS_CONFIG);

    renderGitSettingsScreen();
    await screen.findByTestId("git-settings-screen");

    const submit = await screen.findByTestId("submit-button");
    expect(submit).toBeDisabled();

    const githubInput = await screen.findByTestId("github-token-input");
    await userEvent.type(githubInput, "test-token");
    expect(submit).not.toBeDisabled();

    // submit the form
    await userEvent.click(submit);
    expect(saveSettingsSpy).toHaveBeenCalled();
    expect(submit).toBeDisabled();

    const gitlabInput = await screen.findByTestId("gitlab-token-input");
    await userEvent.type(gitlabInput, "test-token");
    expect(gitlabInput).toHaveValue("test-token");
    expect(submit).not.toBeDisabled();

    // submit the form
    await userEvent.click(submit);
    expect(saveSettingsSpy).toHaveBeenCalled();

    await waitFor(() => expect(submit).toBeDisabled());
  });
});

describe("Status toasts", () => {
  it("should call displaySuccessToast when the settings are saved", async () => {
    const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    getSettingsSpy.mockResolvedValue(MOCK_DEFAULT_USER_SETTINGS);

    const displaySuccessToastSpy = vi.spyOn(
      ToastHandlers,
      "displaySuccessToast",
    );

    renderGitSettingsScreen();

    // Toggle setting to change
    const githubInput = await screen.findByTestId("github-token-input");
    await userEvent.type(githubInput, "test-token");

    const submit = await screen.findByTestId("submit-button");
    await userEvent.click(submit);

    expect(saveSettingsSpy).toHaveBeenCalled();
    await waitFor(() => expect(displaySuccessToastSpy).toHaveBeenCalled());
  });

  it("should call displayErrorToast when the settings fail to save", async () => {
    const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    getSettingsSpy.mockResolvedValue(MOCK_DEFAULT_USER_SETTINGS);

    const displayErrorToastSpy = vi.spyOn(ToastHandlers, "displayErrorToast");

    saveSettingsSpy.mockRejectedValue(new Error("Failed to save settings"));

    renderGitSettingsScreen();

    // Toggle setting to change
    const gitlabInput = await screen.findByTestId("gitlab-token-input");
    await userEvent.type(gitlabInput, "test-token");

    const submit = await screen.findByTestId("submit-button");
    await userEvent.click(submit);

    expect(saveSettingsSpy).toHaveBeenCalled();
    expect(displayErrorToastSpy).toHaveBeenCalled();
  });
});
