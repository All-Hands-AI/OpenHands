import { render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { createRoutesStub } from "react-router";
import { Provider } from "react-redux";
import { createAxiosNotFoundErrorObject, setupStore } from "test-utils";
import HomeScreen from "#/routes/home";
import { GitRepository } from "#/types/git";
import OpenHands from "#/api/open-hands";
import MainApp from "#/routes/root-layout";
import { MOCK_DEFAULT_USER_SETTINGS } from "#/mocks/handlers";

const RouterStub = createRoutesStub([
  {
    Component: MainApp,
    path: "/",
    children: [
      {
        Component: HomeScreen,
        path: "/",
      },
      {
        Component: () => <div data-testid="conversation-screen" />,
        path: "/conversations/:conversationId",
      },
      {
        Component: () => <div data-testid="settings-screen" />,
        path: "/settings",
      },
    ],
  },
]);

const selectRepository = async (repoName: string) => {
  const repoConnector = screen.getByTestId("repo-connector");

  // First select the provider
  const providerDropdown = await waitFor(() =>
    screen.getByText("Select Provider"),
  );
  await userEvent.click(providerDropdown);
  await userEvent.click(screen.getByText("Github"));

  // Then select the repository
  const dropdown = within(repoConnector).getByTestId("repo-dropdown");
  const repoInput = within(dropdown).getByRole("combobox");
  await userEvent.click(repoInput);

  // Wait for the options to be loaded and displayed
  await waitFor(() => {
    const options = screen.getAllByText(repoName);
    // Find the option in the dropdown (it will have role="option")
    const dropdownOption = options.find(
      (el) => el.getAttribute("role") === "option",
    );
    expect(dropdownOption).toBeInTheDocument();
  });
  const options = screen.getAllByText(repoName);
  const dropdownOption = options.find(
    (el) => el.getAttribute("role") === "option",
  );
  await userEvent.click(dropdownOption!);

  // Wait for the branch to be auto-selected
  await waitFor(() => {
    expect(screen.getByText("main")).toBeInTheDocument();
  });
};

const renderHomeScreen = () =>
  render(<RouterStub />, {
    wrapper: ({ children }) => (
      <Provider store={setupStore()}>
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      </Provider>
    ),
  });

const MOCK_RESPOSITORIES: GitRepository[] = [
  {
    id: "1",
    full_name: "octocat/hello-world",
    git_provider: "github",
    is_public: true,
  },
  {
    id: "2",
    full_name: "octocat/earth",
    git_provider: "github",
    is_public: true,
  },
];

describe("HomeScreen", () => {
  beforeEach(() => {
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      provider_tokens_set: {
        github: null,
        gitlab: null,
      },
    });
  });

  it("should render", () => {
    renderHomeScreen();
    screen.getByTestId("home-screen");
  });

  it("should render the repository connector and suggested tasks sections", async () => {
    renderHomeScreen();

    await waitFor(() => {
      screen.getByTestId("repo-connector");
      screen.getByTestId("task-suggestions");
    });
  });

  it("should have responsive layout for mobile and desktop screens", async () => {
    renderHomeScreen();

    const mainContainer = screen
      .getByTestId("home-screen")
      .querySelector("main");
    expect(mainContainer).toHaveClass("flex", "flex-col", "lg:flex-row");
  });

  // TODO: Fix this test
  it.skip("should filter and reset the suggested tasks based on repository selection", async () => {});

  describe("launch buttons", () => {
    const setupLaunchButtons = async () => {
      let headerLaunchButton = screen.getByTestId("header-launch-button");
      let repoLaunchButton = await screen.findByTestId("repo-launch-button");
      let tasksLaunchButtons =
        await screen.findAllByTestId("task-launch-button");

      // Mock the repository branches API call
      vi.spyOn(OpenHands, "getRepositoryBranches").mockResolvedValue([
        { name: "main", commit_sha: "123", protected: false },
        { name: "develop", commit_sha: "456", protected: false },
      ]);

      // Select a repository to enable the repo launch button
      await selectRepository("octocat/hello-world");

      // Wait for all buttons to be enabled
      await waitFor(() => {
        expect(headerLaunchButton).not.toBeDisabled();
        expect(repoLaunchButton).not.toBeDisabled();
        tasksLaunchButtons.forEach((button) => {
          expect(button).not.toBeDisabled();
        });
      });

      // Get fresh references to the buttons
      headerLaunchButton = screen.getByTestId("header-launch-button");
      repoLaunchButton = screen.getByTestId("repo-launch-button");
      tasksLaunchButtons = await screen.findAllByTestId("task-launch-button");

      return {
        headerLaunchButton,
        repoLaunchButton,
        tasksLaunchButtons,
      };
    };

    beforeEach(() => {
      const retrieveUserGitRepositoriesSpy = vi.spyOn(
        OpenHands,
        "retrieveUserGitRepositories",
      );
      retrieveUserGitRepositoriesSpy.mockResolvedValue({
        data: MOCK_RESPOSITORIES,
        nextPage: null,
      });
    });

    it("should disable the other launch buttons when the header launch button is clicked", async () => {
      renderHomeScreen();
      const { headerLaunchButton, repoLaunchButton } =
        await setupLaunchButtons();

      const tasksLaunchButtonsAfter =
        await screen.findAllByTestId("task-launch-button");

      // All other buttons should be disabled when the header button is clicked
      await userEvent.click(headerLaunchButton);

      await waitFor(() => {
        expect(headerLaunchButton).toBeDisabled();
        expect(repoLaunchButton).toBeDisabled();
        tasksLaunchButtonsAfter.forEach((button) => {
          expect(button).toBeDisabled();
        });
      });
    });

    it("should disable the other launch buttons when the repo launch button is clicked", async () => {
      renderHomeScreen();
      const { headerLaunchButton, repoLaunchButton } =
        await setupLaunchButtons();

      const tasksLaunchButtonsAfter =
        await screen.findAllByTestId("task-launch-button");

      // All other buttons should be disabled when the repo button is clicked
      await userEvent.click(repoLaunchButton);

      await waitFor(() => {
        expect(headerLaunchButton).toBeDisabled();
        expect(repoLaunchButton).toBeDisabled();
        tasksLaunchButtonsAfter.forEach((button) => {
          expect(button).toBeDisabled();
        });
      });
    });

    it("should disable the other launch buttons when any task launch button is clicked", async () => {
      renderHomeScreen();
      const { headerLaunchButton, repoLaunchButton, tasksLaunchButtons } =
        await setupLaunchButtons();

      const tasksLaunchButtonsAfter =
        await screen.findAllByTestId("task-launch-button");

      // All other buttons should be disabled when the task button is clicked
      await userEvent.click(tasksLaunchButtons[0]);

      await waitFor(() => {
        expect(headerLaunchButton).toBeDisabled();
        expect(repoLaunchButton).toBeDisabled();
        tasksLaunchButtonsAfter.forEach((button) => {
          expect(button).toBeDisabled();
        });
      });
    });
  });

  it("should hide the suggested tasks section if not authed with git(hub|lab)", async () => {
    renderHomeScreen();

    const taskSuggestions = screen.queryByTestId("task-suggestions");
    const repoConnector = screen.getByTestId("repo-connector");

    expect(taskSuggestions).not.toBeInTheDocument();
    expect(repoConnector).toBeInTheDocument();
  });
});

describe("Settings 404", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
  const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");

  it("should open the settings modal if GET /settings fails with a 404", async () => {
    const error = createAxiosNotFoundErrorObject();
    getSettingsSpy.mockRejectedValue(error);

    renderHomeScreen();

    const settingsModal = await screen.findByTestId("ai-config-modal");
    expect(settingsModal).toBeInTheDocument();
  });

  it("should navigate to the settings screen when clicking the advanced settings button", async () => {
    const error = createAxiosNotFoundErrorObject();
    getSettingsSpy.mockRejectedValue(error);

    const user = userEvent.setup();
    renderHomeScreen();

    const settingsScreen = screen.queryByTestId("settings-screen");
    expect(settingsScreen).not.toBeInTheDocument();

    const settingsModal = await screen.findByTestId("ai-config-modal");
    expect(settingsModal).toBeInTheDocument();

    const advancedSettingsButton = await screen.findByTestId(
      "advanced-settings-link",
    );
    await user.click(advancedSettingsButton);

    const settingsScreenAfter = await screen.findByTestId("settings-screen");
    expect(settingsScreenAfter).toBeInTheDocument();

    const settingsModalAfter = screen.queryByTestId("ai-config-modal");
    expect(settingsModalAfter).not.toBeInTheDocument();
  });

  it("should not open the settings modal if GET /settings fails but is SaaS mode", async () => {
    // @ts-expect-error - we only need APP_MODE for this test
    getConfigSpy.mockResolvedValue({
      APP_MODE: "saas",
      FEATURE_FLAGS: {
        ENABLE_BILLING: false,
        HIDE_LLM_SETTINGS: false,
        ENABLE_JIRA: false,
        ENABLE_JIRA_DC: false,
        ENABLE_LINEAR: false,
      },
    });
    const error = createAxiosNotFoundErrorObject();
    getSettingsSpy.mockRejectedValue(error);

    renderHomeScreen();

    expect(screen.queryByTestId("ai-config-modal")).not.toBeInTheDocument();
  });
});

describe("Setup Payment modal", () => {
  const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
  const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");

  it("should only render if SaaS mode and is new user", async () => {
    // @ts-expect-error - we only need the APP_MODE for this test
    getConfigSpy.mockResolvedValue({
      APP_MODE: "saas",
      FEATURE_FLAGS: {
        ENABLE_BILLING: true,
        HIDE_LLM_SETTINGS: false,
        ENABLE_JIRA: false,
        ENABLE_JIRA_DC: false,
        ENABLE_LINEAR: false,
      },
    });
    const error = createAxiosNotFoundErrorObject();
    getSettingsSpy.mockRejectedValue(error);

    renderHomeScreen();

    const setupPaymentModal = await screen.findByTestId(
      "proceed-to-stripe-button",
    );
    expect(setupPaymentModal).toBeInTheDocument();
  });
});
