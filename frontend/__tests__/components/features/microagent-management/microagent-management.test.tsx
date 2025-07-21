import { screen, waitFor, within } from "@testing-library/react";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClientConfig } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { createRoutesStub } from "react-router";
import React from "react";
import { renderWithProviders } from "test-utils";
import MicroagentManagement from "#/routes/microagent-management";
import OpenHands from "#/api/open-hands";
import { GitRepository } from "#/types/git";
import { RepositoryMicroagent } from "#/types/microagent-management";

describe("MicroagentManagement", () => {
  const RouterStub = createRoutesStub([
    {
      Component: MicroagentManagement,
      path: "/",
    },
  ]);

  const renderMicroagentManagement = (config?: QueryClientConfig) =>
    renderWithProviders(<RouterStub />, {
      preloadedState: {
        metrics: {
          cost: null,
          max_budget_per_task: null,
          usage: null,
        },
        microagentManagement: {
          selectedMicroagent: null,
          addMicroagentModalVisible: false,
          selectedRepository: null,
          personalRepositories: [],
          organizationRepositories: [],
          repositories: [],
        },
      },
    });

  beforeAll(() => {
    vi.mock("react-router", async (importOriginal) => ({
      ...(await importOriginal<typeof import("react-router")>()),
      Link: ({ children }: React.PropsWithChildren) => children,
      useNavigate: vi.fn(() => vi.fn()),
      useLocation: vi.fn(() => ({ pathname: "/microagent-management" })),
      useParams: vi.fn(() => ({ conversationId: "2" })),
    }));
  });

  const mockRepositories: GitRepository[] = [
    {
      id: "1",
      full_name: "user/repo1",
      git_provider: "github",
      is_public: true,
      owner_type: "user",
      pushed_at: "2021-10-01T12:00:00Z",
    },
    {
      id: "2",
      full_name: "user/repo2/.openhands",
      git_provider: "github",
      is_public: true,
      owner_type: "user",
      pushed_at: "2021-10-02T12:00:00Z",
    },
    {
      id: "3",
      full_name: "org/repo3/.openhands",
      git_provider: "github",
      is_public: true,
      owner_type: "organization",
      pushed_at: "2021-10-03T12:00:00Z",
    },
    {
      id: "4",
      full_name: "user/repo4",
      git_provider: "github",
      is_public: true,
      owner_type: "user",
      pushed_at: "2021-10-04T12:00:00Z",
    },
  ];

  const mockMicroagents: RepositoryMicroagent[] = [
    {
      name: "test-microagent-1",
      type: "repo",
      content: "Test microagent content 1",
      triggers: ["test", "microagent"],
      inputs: [],
      tools: [],
      created_at: "2021-10-01T12:00:00Z",
      git_provider: "github",
    },
    {
      name: "test-microagent-2",
      type: "knowledge",
      content: "Test microagent content 2",
      triggers: ["knowledge", "test"],
      inputs: [],
      tools: [],
      created_at: "2021-10-02T12:00:00Z",
      git_provider: "github",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.restoreAllMocks();
    // Setup default mock for retrieveUserGitRepositories
    vi.spyOn(OpenHands, "retrieveUserGitRepositories").mockResolvedValue([
      ...mockRepositories,
    ]);
    // Setup default mock for getRepositoryMicroagents
    vi.spyOn(OpenHands, "getRepositoryMicroagents").mockResolvedValue([
      ...mockMicroagents,
    ]);
  });

  it("should render the microagent management page", async () => {
    renderMicroagentManagement();

    // Check that the main title is rendered
    await screen.findByText("MICROAGENT_MANAGEMENT$DESCRIPTION");
  });

  it("should display loading state when fetching repositories", async () => {
    const retrieveUserGitRepositoriesSpy = vi.spyOn(
      OpenHands,
      "retrieveUserGitRepositories",
    );
    retrieveUserGitRepositoriesSpy.mockImplementation(
      () => new Promise(() => {}), // Never resolves
    );

    renderMicroagentManagement();

    // Check that loading spinner is displayed
    const loadingSpinner = await screen.findByText("HOME$LOADING_REPOSITORIES");
    expect(loadingSpinner).toBeInTheDocument();
  });

  it("should handle error when fetching repositories", async () => {
    const retrieveUserGitRepositoriesSpy = vi.spyOn(
      OpenHands,
      "retrieveUserGitRepositories",
    );
    retrieveUserGitRepositoriesSpy.mockRejectedValue(
      new Error("Failed to fetch repositories"),
    );

    renderMicroagentManagement();

    // Wait for the error to be handled
    await waitFor(() => {
      expect(retrieveUserGitRepositoriesSpy).toHaveBeenCalled();
    });
  });

  it("should categorize repositories correctly", async () => {
    renderMicroagentManagement();

    // Wait for repositories to be loaded
    await waitFor(() => {
      expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
    });

    // Check that tabs are rendered
    const personalTab = screen.getByText("COMMON$PERSONAL");
    const repositoriesTab = screen.getByText("COMMON$REPOSITORIES");
    const organizationsTab = screen.getByText("COMMON$ORGANIZATIONS");

    expect(personalTab).toBeInTheDocument();
    expect(repositoriesTab).toBeInTheDocument();
    expect(organizationsTab).toBeInTheDocument();
  });

  it("should display repositories in accordion", async () => {
    renderMicroagentManagement();

    // Wait for repositories to be loaded and rendered
    await waitFor(() => {
      expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
    });

    // Check that repository names are displayed
    const repo1 = screen.getByText("user/repo2/.openhands");
    expect(repo1).toBeInTheDocument();
  });

  it("should expand repository accordion and show microagents", async () => {
    const user = userEvent.setup();
    renderMicroagentManagement();

    // Wait for repositories to be loaded
    await waitFor(() => {
      expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
    });

    // Find and click on the first repository accordion
    const repoAccordion = screen.getByText("user/repo2/.openhands");
    await user.click(repoAccordion);

    // Wait for microagents to be fetched
    await waitFor(() => {
      expect(OpenHands.getRepositoryMicroagents).toHaveBeenCalledWith(
        "user",
        "repo2",
      );
    });

    // Check that microagents are displayed
    const microagent1 = screen.getByText("test-microagent-1");
    const microagent2 = screen.getByText("test-microagent-2");

    expect(microagent1).toBeInTheDocument();
    expect(microagent2).toBeInTheDocument();
  });

  it("should display loading state when fetching microagents", async () => {
    const user = userEvent.setup();
    const getRepositoryMicroagentsSpy = vi.spyOn(
      OpenHands,
      "getRepositoryMicroagents",
    );
    getRepositoryMicroagentsSpy.mockImplementation(
      () => new Promise(() => {}), // Never resolves
    );

    renderMicroagentManagement();

    // Wait for repositories to be loaded
    await waitFor(() => {
      expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
    });

    // Find and click on the first repository accordion
    const repoAccordion = screen.getByText("user/repo2/.openhands");
    await user.click(repoAccordion);

    // Check that loading spinner is displayed
    const loadingSpinner = screen.getByTestId("loading-spinner");
    expect(loadingSpinner).toBeInTheDocument();
  });

  it("should handle error when fetching microagents", async () => {
    const user = userEvent.setup();
    const getRepositoryMicroagentsSpy = vi.spyOn(
      OpenHands,
      "getRepositoryMicroagents",
    );
    getRepositoryMicroagentsSpy.mockRejectedValue(
      new Error("Failed to fetch microagents"),
    );

    renderMicroagentManagement();

    // Wait for repositories to be loaded
    await waitFor(() => {
      expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
    });

    // Find and click on the first repository accordion
    const repoAccordion = screen.getByText("user/repo2/.openhands");
    await user.click(repoAccordion);

    // Wait for the error to be handled
    await waitFor(() => {
      expect(getRepositoryMicroagentsSpy).toHaveBeenCalledWith("user", "repo2");
    });
  });

  it("should display empty state when no microagents are found", async () => {
    const user = userEvent.setup();
    const getRepositoryMicroagentsSpy = vi.spyOn(
      OpenHands,
      "getRepositoryMicroagents",
    );
    getRepositoryMicroagentsSpy.mockResolvedValue([]);

    renderMicroagentManagement();

    // Wait for repositories to be loaded
    await waitFor(() => {
      expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
    });

    // Find and click on the first repository accordion
    const repoAccordion = screen.getByText("user/repo2/.openhands");
    await user.click(repoAccordion);

    // Wait for microagents to be fetched
    await waitFor(() => {
      expect(getRepositoryMicroagentsSpy).toHaveBeenCalledWith("user", "repo2");
    });

    // Check that the learn this repo component is displayed
    const learnThisRepo = screen.getByText(
      "MICROAGENT_MANAGEMENT$LEARN_THIS_REPO",
    );
    expect(learnThisRepo).toBeInTheDocument();
  });

  it("should display microagent cards with correct information", async () => {
    const user = userEvent.setup();
    renderMicroagentManagement();

    // Wait for repositories to be loaded
    await waitFor(() => {
      expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
    });

    // Find and click on the first repository accordion
    const repoAccordion = screen.getByText("user/repo2/.openhands");
    await user.click(repoAccordion);

    // Wait for microagents to be fetched
    await waitFor(() => {
      expect(OpenHands.getRepositoryMicroagents).toHaveBeenCalledWith(
        "user",
        "repo2",
      );
    });

    // Check that microagent cards display correct information
    const microagent1 = screen.getByText("test-microagent-1");
    const microagent2 = screen.getByText("test-microagent-2");

    expect(microagent1).toBeInTheDocument();
    expect(microagent2).toBeInTheDocument();

    // Check that microagent file paths are displayed
    const filePath1 = screen.getByText(
      ".openhands/microagents/test-microagent-1",
    );
    const filePath2 = screen.getByText(
      ".openhands/microagents/test-microagent-2",
    );

    expect(filePath1).toBeInTheDocument();
    expect(filePath2).toBeInTheDocument();
  });

  it("should display add microagent button in repository accordion", async () => {
    renderMicroagentManagement();

    // Wait for repositories to be loaded
    await waitFor(() => {
      expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
    });

    // Check that add microagent buttons are present
    const addButtons = screen.getAllByText("COMMON$ADD_MICROAGENT");
    expect(addButtons.length).toBeGreaterThan(0);
  });

  it("should open add microagent modal when add button is clicked", async () => {
    const user = userEvent.setup();
    renderMicroagentManagement();

    // Wait for repositories to be loaded
    await waitFor(() => {
      expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
    });

    // Find and click the first add microagent button
    const addButtons = screen.getAllByText("COMMON$ADD_MICROAGENT");
    await user.click(addButtons[0]);

    // Check that the modal is opened
    const modalTitle = screen.getByText(
      "MICROAGENT_MANAGEMENT$ADD_A_MICROAGENT",
    );
    expect(modalTitle).toBeInTheDocument();
  });

  it("should close add microagent modal when cancel is clicked", async () => {
    const user = userEvent.setup();
    renderMicroagentManagement();

    // Wait for repositories to be loaded
    await waitFor(() => {
      expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
    });

    // Find and click the first add microagent button
    const addButtons = screen.getAllByText("COMMON$ADD_MICROAGENT");
    await user.click(addButtons[0]);

    // Check that the modal is opened
    const modalTitle = screen.getByText(
      "MICROAGENT_MANAGEMENT$ADD_A_MICROAGENT",
    );
    expect(modalTitle).toBeInTheDocument();

    // Find and click the cancel button
    const cancelButton = screen.getByRole("button", { name: /cancel/i });
    await user.click(cancelButton);

    // Check that the modal is closed
    expect(
      screen.queryByText("MICROAGENT_MANAGEMENT$ADD_A_MICROAGENT"),
    ).not.toBeInTheDocument();
  });

  it("should display empty state when no repositories are found", async () => {
    const retrieveUserGitRepositoriesSpy = vi.spyOn(
      OpenHands,
      "retrieveUserGitRepositories",
    );
    retrieveUserGitRepositoriesSpy.mockResolvedValue([]);

    renderMicroagentManagement();

    // Wait for repositories to be loaded
    await waitFor(() => {
      expect(retrieveUserGitRepositoriesSpy).toHaveBeenCalled();
    });

    // Check that empty state messages are displayed
    const personalEmptyState = screen.getByText(
      "MICROAGENT_MANAGEMENT$YOU_DO_NOT_HAVE_USER_LEVEL_MICROAGENTS",
    );

    expect(personalEmptyState).toBeInTheDocument();
  });

  it("should handle multiple repository expansions", async () => {
    const user = userEvent.setup();
    renderMicroagentManagement();

    // Wait for repositories to be loaded
    await waitFor(() => {
      expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
    });

    // Find and click on the first repository accordion
    const repoAccordion1 = screen.getByText("user/repo2/.openhands");
    await user.click(repoAccordion1);

    // Wait for microagents to be fetched for first repo
    await waitFor(() => {
      expect(OpenHands.getRepositoryMicroagents).toHaveBeenCalledWith(
        "user",
        "repo2",
      );
    });

    // Check that the API call was made
    expect(OpenHands.getRepositoryMicroagents).toHaveBeenCalledTimes(1);
  });

  it("should display ready to add microagent message in main area", async () => {
    renderMicroagentManagement();

    // Check that the main area shows the ready message
    const readyMessage = screen.getByText(
      "MICROAGENT_MANAGEMENT$READY_TO_ADD_MICROAGENT",
    );
    const descriptionMessage = screen.getByText(
      "MICROAGENT_MANAGEMENT$OPENHANDS_CAN_LEARN_ABOUT_REPOSITORIES",
    );

    expect(readyMessage).toBeInTheDocument();
    expect(descriptionMessage).toBeInTheDocument();
  });
});
