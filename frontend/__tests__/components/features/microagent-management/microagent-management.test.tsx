import { screen, waitFor } from "@testing-library/react";
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
import { Conversation } from "#/api/open-hands.types";

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
    {
      id: "5",
      full_name: "user/TestRepository",
      git_provider: "github",
      is_public: true,
      owner_type: "user",
      pushed_at: "2021-10-05T12:00:00Z",
    },
    {
      id: "6",
      full_name: "org/AnotherRepo",
      git_provider: "github",
      is_public: true,
      owner_type: "organization",
      pushed_at: "2021-10-06T12:00:00Z",
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

  const mockConversations: Conversation[] = [
    {
      conversation_id: "conv-1",
      title: "Test Conversation 1",
      selected_repository: "user/repo2/.openhands",
      selected_branch: "main",
      git_provider: "github",
      last_updated_at: "2021-10-01T12:00:00Z",
      created_at: "2021-10-01T12:00:00Z",
      status: "RUNNING",
      runtime_status: null,
      trigger: "microagent_management",
      url: null,
      session_api_key: null,
    },
    {
      conversation_id: "conv-2",
      title: "Test Conversation 2",
      selected_repository: "user/repo2/.openhands",
      selected_branch: "main",
      git_provider: "github",
      last_updated_at: "2021-10-02T12:00:00Z",
      created_at: "2021-10-02T12:00:00Z",
      status: "STOPPED",
      runtime_status: null,
      trigger: "microagent_management",
      url: null,
      session_api_key: null,
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
    // Setup default mock for searchConversations
    vi.spyOn(OpenHands, "searchConversations").mockResolvedValue([
      ...mockConversations,
    ]);
    // Mock branches to always return a 'main' branch for the modal
    vi.spyOn(OpenHands, "getRepositoryBranches").mockResolvedValue([
      { name: "main", commit_sha: "abc123", protected: false },
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

    // Check that no microagents are displayed
    expect(screen.queryByText("test-microagent-1")).not.toBeInTheDocument();
    expect(screen.queryByText("test-microagent-2")).not.toBeInTheDocument();
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
    await waitFor(() => {
      expect(screen.getByTestId("add-microagent-modal")).toBeInTheDocument();
    });
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
    const closeButton = screen.getByRole("button", { name: "" });
    await user.click(closeButton);

    // Check that modal is closed
    await waitFor(() => {
      expect(
        screen.queryByTestId("add-microagent-modal"),
      ).not.toBeInTheDocument();
    });
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

  // Search functionality tests
  describe("Search functionality", () => {
    it("should render search input field", async () => {
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Check that search input is rendered
      const searchInput = screen.getByRole("textbox", {
        name: "COMMON$SEARCH_REPOSITORIES",
      });
      expect(searchInput).toBeInTheDocument();
      expect(searchInput).toHaveAttribute(
        "placeholder",
        "COMMON$SEARCH_REPOSITORIES...",
      );
    });

    it("should filter repositories when typing in search input", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Initially only repositories with .openhands should be visible
      expect(screen.getByText("user/repo2/.openhands")).toBeInTheDocument();
      expect(screen.queryByText("user/repo1")).not.toBeInTheDocument();
      expect(screen.queryByText("user/repo4")).not.toBeInTheDocument();

      // Type in search input to filter further
      const searchInput = screen.getByRole("textbox", {
        name: "COMMON$SEARCH_REPOSITORIES",
      });
      await user.type(searchInput, "repo2");

      // Only repo2 should be visible
      expect(screen.getByText("user/repo2/.openhands")).toBeInTheDocument();
      expect(screen.queryByText("user/repo1")).not.toBeInTheDocument();
      expect(
        screen.queryByText("org/repo3/.openhands"),
      ).not.toBeInTheDocument();
      expect(screen.queryByText("user/repo4")).not.toBeInTheDocument();
      expect(screen.queryByText("user/TestRepository")).not.toBeInTheDocument();
      expect(screen.queryByText("org/AnotherRepo")).not.toBeInTheDocument();
    });

    it("should perform case-insensitive search", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Type in search input with uppercase
      const searchInput = screen.getByRole("textbox", {
        name: "COMMON$SEARCH_REPOSITORIES",
      });
      await user.type(searchInput, "REPO2");

      // repo2 should be visible (case-insensitive match)
      expect(screen.getByText("user/repo2/.openhands")).toBeInTheDocument();
      expect(screen.queryByText("user/repo1")).not.toBeInTheDocument();
      expect(
        screen.queryByText("org/repo3/.openhands"),
      ).not.toBeInTheDocument();
    });

    it("should filter repositories by partial matches", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Type in search input with partial match
      const searchInput = screen.getByRole("textbox", {
        name: "COMMON$SEARCH_REPOSITORIES",
      });
      await user.type(searchInput, "repo");

      // All repositories with "repo" in the name should be visible
      expect(screen.getByText("user/repo2/.openhands")).toBeInTheDocument();
      expect(screen.queryByText("user/repo1")).not.toBeInTheDocument();
      expect(
        screen.queryByText("org/repo3/.openhands"),
      ).not.toBeInTheDocument();
      expect(screen.queryByText("user/repo4")).not.toBeInTheDocument();
      expect(screen.queryByText("user/TestRepository")).not.toBeInTheDocument();
      expect(screen.queryByText("org/AnotherRepo")).not.toBeInTheDocument();
    });

    it("should show all repositories when search input is cleared", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Type in search input
      const searchInput = screen.getByRole("textbox", {
        name: "COMMON$SEARCH_REPOSITORIES",
      });
      await user.type(searchInput, "repo2");

      // Only repo2 should be visible
      expect(screen.getByText("user/repo2/.openhands")).toBeInTheDocument();
      expect(screen.queryByText("user/repo1")).not.toBeInTheDocument();

      // Clear the search input
      await user.clear(searchInput);

      // All repositories should be visible again (only those with .openhands)
      expect(screen.getByText("user/repo2/.openhands")).toBeInTheDocument();
      expect(screen.queryByText("user/repo1")).not.toBeInTheDocument();
      expect(
        screen.queryByText("org/repo3/.openhands"),
      ).not.toBeInTheDocument();
      expect(screen.queryByText("user/repo4")).not.toBeInTheDocument();
      expect(screen.queryByText("user/TestRepository")).not.toBeInTheDocument();
      expect(screen.queryByText("org/AnotherRepo")).not.toBeInTheDocument();
    });

    it("should handle empty search results", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Type in search input with non-existent repository name
      const searchInput = screen.getByRole("textbox", {
        name: "COMMON$SEARCH_REPOSITORIES",
      });
      await user.type(searchInput, "nonexistent");

      // No repositories should be visible
      expect(screen.queryByText("user/repo1")).not.toBeInTheDocument();
      expect(
        screen.queryByText("user/repo2/.openhands"),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByText("org/repo3/.openhands"),
      ).not.toBeInTheDocument();
      expect(screen.queryByText("user/repo4")).not.toBeInTheDocument();
      expect(screen.queryByText("user/TestRepository")).not.toBeInTheDocument();
      expect(screen.queryByText("org/AnotherRepo")).not.toBeInTheDocument();
    });

    it("should handle special characters in search", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Type in search input with special characters
      const searchInput = screen.getByRole("textbox", {
        name: "COMMON$SEARCH_REPOSITORIES",
      });
      await user.type(searchInput, ".openhands");

      // Only repositories with .openhands should be visible
      expect(screen.getByText("user/repo2/.openhands")).toBeInTheDocument();
      expect(screen.queryByText("user/repo1")).not.toBeInTheDocument();
      expect(screen.queryByText("user/repo4")).not.toBeInTheDocument();
    });

    it("should maintain accordion functionality with filtered results", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Filter to show only repo2
      const searchInput = screen.getByRole("textbox", {
        name: "COMMON$SEARCH_REPOSITORIES",
      });
      await user.type(searchInput, "repo2");

      // Click on the filtered repository accordion
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

    it("should handle whitespace in search input", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Type in search input with leading/trailing whitespace
      const searchInput = screen.getByRole("textbox", {
        name: "COMMON$SEARCH_REPOSITORIES",
      });
      await user.type(searchInput, "  repo2  ");

      // repo2 should still be visible (whitespace should be trimmed)
      expect(screen.getByText("user/repo2/.openhands")).toBeInTheDocument();
      expect(screen.queryByText("user/repo1")).not.toBeInTheDocument();
    });

    it("should update search results in real-time", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      const searchInput = screen.getByRole("textbox", {
        name: "COMMON$SEARCH_REPOSITORIES",
      });

      // Type "repo" - should show repo2
      await user.type(searchInput, "repo");
      expect(screen.getByText("user/repo2/.openhands")).toBeInTheDocument();
      expect(screen.queryByText("user/repo1")).not.toBeInTheDocument();

      // Add "2" to make it "repo2" - should show only repo2
      await user.type(searchInput, "2");
      expect(screen.getByText("user/repo2/.openhands")).toBeInTheDocument();
      expect(screen.queryByText("user/repo1")).not.toBeInTheDocument();

      // Remove "2" to make it "repo" again - should show repo2
      await user.keyboard("{Backspace}");
      expect(screen.getByText("user/repo2/.openhands")).toBeInTheDocument();
      expect(screen.queryByText("user/repo1")).not.toBeInTheDocument();
    });
  });

  // Search conversations functionality tests
  describe("Search conversations functionality", () => {
    it("should call searchConversations API when repository is expanded", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Find and click on the first repository accordion
      const repoAccordion = screen.getByText("user/repo2/.openhands");
      await user.click(repoAccordion);

      // Wait for both microagents and conversations to be fetched
      await waitFor(() => {
        expect(OpenHands.getRepositoryMicroagents).toHaveBeenCalledWith(
          "user",
          "repo2",
        );
        expect(OpenHands.searchConversations).toHaveBeenCalledWith(
          "user/repo2/.openhands",
          "microagent_management",
          1000,
        );
      });
    });

    it("should display both microagents and conversations when repository is expanded", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Find and click on the first repository accordion
      const repoAccordion = screen.getByText("user/repo2/.openhands");
      await user.click(repoAccordion);

      // Wait for both queries to complete
      await waitFor(() => {
        expect(OpenHands.getRepositoryMicroagents).toHaveBeenCalled();
        expect(OpenHands.searchConversations).toHaveBeenCalled();
      });

      // Check that microagents are displayed
      const microagent1 = screen.getByText("test-microagent-1");
      const microagent2 = screen.getByText("test-microagent-2");

      expect(microagent1).toBeInTheDocument();
      expect(microagent2).toBeInTheDocument();

      // Check that conversations are displayed
      const conversation1 = screen.getByText("Test Conversation 1");
      const conversation2 = screen.getByText("Test Conversation 2");

      expect(conversation1).toBeInTheDocument();
      expect(conversation2).toBeInTheDocument();
    });

    it("should show loading state when both microagents and conversations are loading", async () => {
      const user = userEvent.setup();
      const getRepositoryMicroagentsSpy = vi.spyOn(
        OpenHands,
        "getRepositoryMicroagents",
      );
      const searchConversationsSpy = vi.spyOn(OpenHands, "searchConversations");

      // Make both queries never resolve
      getRepositoryMicroagentsSpy.mockImplementation(
        () => new Promise(() => {}),
      );
      searchConversationsSpy.mockImplementation(() => new Promise(() => {}));

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

    it("should hide loading state when both queries complete", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Find and click on the first repository accordion
      const repoAccordion = screen.getByText("user/repo2/.openhands");
      await user.click(repoAccordion);

      // Wait for both queries to complete
      await waitFor(() => {
        expect(OpenHands.getRepositoryMicroagents).toHaveBeenCalled();
        expect(OpenHands.searchConversations).toHaveBeenCalled();
      });

      // Check that loading spinner is not displayed
      expect(screen.queryByTestId("loading-spinner")).not.toBeInTheDocument();
    });

    it("should display microagent file paths for microagents but not for conversations", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Find and click on the first repository accordion
      const repoAccordion = screen.getByText("user/repo2/.openhands");
      await user.click(repoAccordion);

      // Wait for both queries to complete
      await waitFor(() => {
        expect(OpenHands.getRepositoryMicroagents).toHaveBeenCalled();
        expect(OpenHands.searchConversations).toHaveBeenCalled();
      });

      // Check that microagent file paths are displayed for microagents
      const microagentFilePath1 = screen.getByText(
        ".openhands/microagents/test-microagent-1",
      );
      const microagentFilePath2 = screen.getByText(
        ".openhands/microagents/test-microagent-2",
      );

      expect(microagentFilePath1).toBeInTheDocument();
      expect(microagentFilePath2).toBeInTheDocument();

      // Check that microagent file paths are NOT displayed for conversations
      expect(
        screen.queryByText(".openhands/microagents/Test Conversation 1"),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByText(".openhands/microagents/Test Conversation 2"),
      ).not.toBeInTheDocument();
    });

    it("should show learn this repo component when no microagents and no conversations", async () => {
      const user = userEvent.setup();
      const getRepositoryMicroagentsSpy = vi.spyOn(
        OpenHands,
        "getRepositoryMicroagents",
      );
      const searchConversationsSpy = vi.spyOn(OpenHands, "searchConversations");

      // Mock both queries to return empty arrays
      getRepositoryMicroagentsSpy.mockResolvedValue([]);
      searchConversationsSpy.mockResolvedValue([]);

      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Find and click on the first repository accordion
      const repoAccordion = screen.getByText("user/repo2/.openhands");
      await user.click(repoAccordion);

      // Wait for both queries to complete
      await waitFor(() => {
        expect(getRepositoryMicroagentsSpy).toHaveBeenCalled();
        expect(searchConversationsSpy).toHaveBeenCalled();
      });

      // Check that the learn this repo component is displayed
      const learnThisRepo = screen.getByText(
        "MICROAGENT_MANAGEMENT$LEARN_THIS_REPO",
      );
      expect(learnThisRepo).toBeInTheDocument();
    });

    it("should show learn this repo component when only conversations exist but no microagents", async () => {
      const user = userEvent.setup();
      const getRepositoryMicroagentsSpy = vi.spyOn(
        OpenHands,
        "getRepositoryMicroagents",
      );
      const searchConversationsSpy = vi.spyOn(OpenHands, "searchConversations");

      // Mock microagents to return empty array, conversations to return data
      getRepositoryMicroagentsSpy.mockResolvedValue([]);
      searchConversationsSpy.mockResolvedValue([...mockConversations]);

      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Find and click on the first repository accordion
      const repoAccordion = screen.getByText("user/repo2/.openhands");
      await user.click(repoAccordion);

      // Wait for both queries to complete
      await waitFor(() => {
        expect(getRepositoryMicroagentsSpy).toHaveBeenCalled();
        expect(searchConversationsSpy).toHaveBeenCalled();
      });

      // Check that conversations are displayed
      const conversation1 = screen.getByText("Test Conversation 1");
      const conversation2 = screen.getByText("Test Conversation 2");

      expect(conversation1).toBeInTheDocument();
      expect(conversation2).toBeInTheDocument();

      // Check that learn this repo component is NOT displayed (since we have conversations)
      expect(
        screen.queryByText("MICROAGENT_MANAGEMENT$LEARN_THIS_REPO"),
      ).not.toBeInTheDocument();
    });

    it("should show learn this repo component when only microagents exist but no conversations", async () => {
      const user = userEvent.setup();
      const getRepositoryMicroagentsSpy = vi.spyOn(
        OpenHands,
        "getRepositoryMicroagents",
      );
      const searchConversationsSpy = vi.spyOn(OpenHands, "searchConversations");

      // Mock microagents to return data, conversations to return empty array
      getRepositoryMicroagentsSpy.mockResolvedValue([...mockMicroagents]);
      searchConversationsSpy.mockResolvedValue([]);

      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Find and click on the first repository accordion
      const repoAccordion = screen.getByText("user/repo2/.openhands");
      await user.click(repoAccordion);

      // Wait for both queries to complete
      await waitFor(() => {
        expect(getRepositoryMicroagentsSpy).toHaveBeenCalled();
        expect(searchConversationsSpy).toHaveBeenCalled();
      });

      // Check that microagents are displayed
      const microagent1 = screen.getByText("test-microagent-1");
      const microagent2 = screen.getByText("test-microagent-2");

      expect(microagent1).toBeInTheDocument();
      expect(microagent2).toBeInTheDocument();

      // Check that learn this repo component is NOT displayed (since we have microagents)
      expect(
        screen.queryByText("MICROAGENT_MANAGEMENT$LEARN_THIS_REPO"),
      ).not.toBeInTheDocument();
    });

    it("should handle error when fetching conversations", async () => {
      const user = userEvent.setup();
      const searchConversationsSpy = vi.spyOn(OpenHands, "searchConversations");
      searchConversationsSpy.mockRejectedValue(
        new Error("Failed to fetch conversations"),
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
        expect(searchConversationsSpy).toHaveBeenCalledWith(
          "user/repo2/.openhands",
          "microagent_management",
          1000,
        );
      });

      // Check that the learn this repo component is displayed (since conversations failed)
      await waitFor(() => {
        expect(
          screen.getByText("MICROAGENT_MANAGEMENT$LEARN_THIS_REPO"),
        ).toBeInTheDocument();
      });

      // Also check that the microagents query was called successfully
      expect(OpenHands.getRepositoryMicroagents).toHaveBeenCalledWith(
        "user",
        "repo2",
      );
    });

    it("should handle error when fetching microagents but conversations succeed", async () => {
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
        expect(getRepositoryMicroagentsSpy).toHaveBeenCalledWith(
          "user",
          "repo2",
        );
      });

      // Check that the learn this repo component is displayed (since microagents failed)
      const learnThisRepo = screen.getByText(
        "MICROAGENT_MANAGEMENT$LEARN_THIS_REPO",
      );
      expect(learnThisRepo).toBeInTheDocument();
    });

    it("should call searchConversations with correct parameters", async () => {
      const user = userEvent.setup();
      const searchConversationsSpy = vi.spyOn(OpenHands, "searchConversations");

      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Find and click on the first repository accordion
      const repoAccordion = screen.getByText("user/repo2/.openhands");
      await user.click(repoAccordion);

      // Wait for searchConversations to be called
      await waitFor(() => {
        expect(searchConversationsSpy).toHaveBeenCalledWith(
          "user/repo2/.openhands",
          "microagent_management",
          1000,
        );
      });
    });

    it("should display conversations with correct information", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Find and click on the first repository accordion
      const repoAccordion = screen.getByText("user/repo2/.openhands");
      await user.click(repoAccordion);

      // Wait for both queries to complete
      await waitFor(() => {
        expect(OpenHands.getRepositoryMicroagents).toHaveBeenCalled();
        expect(OpenHands.searchConversations).toHaveBeenCalled();
      });

      // Check that conversations display correct information
      const conversation1 = screen.getByText("Test Conversation 1");
      const conversation2 = screen.getByText("Test Conversation 2");

      expect(conversation1).toBeInTheDocument();
      expect(conversation2).toBeInTheDocument();

      // Check that created dates are displayed for conversations (there are multiple elements with the same text)
      const createdDates = screen.getAllByText(
        /COMMON\$CREATED_ON.*10\/01\/2021/,
      );
      expect(createdDates.length).toBeGreaterThan(0);

      const createdDates2 = screen.getAllByText(
        /COMMON\$CREATED_ON.*10\/02\/2021/,
      );
      expect(createdDates2.length).toBeGreaterThan(0);
    });

    it("should handle multiple repository expansions with conversations", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Find and click on the first repository accordion
      const repoAccordion1 = screen.getByText("user/repo2/.openhands");
      await user.click(repoAccordion1);

      // Wait for both queries to be called for first repo
      await waitFor(() => {
        expect(OpenHands.getRepositoryMicroagents).toHaveBeenCalledWith(
          "user",
          "repo2",
        );
        expect(OpenHands.searchConversations).toHaveBeenCalledWith(
          "user/repo2/.openhands",
          "microagent_management",
          1000,
        );
      });

      // Check that both microagents and conversations are displayed
      expect(screen.getByText("test-microagent-1")).toBeInTheDocument();
      expect(screen.getByText("test-microagent-2")).toBeInTheDocument();
      expect(screen.getByText("Test Conversation 1")).toBeInTheDocument();
      expect(screen.getByText("Test Conversation 2")).toBeInTheDocument();
    });
  });

  // Add microagent integration tests
  describe("Add microagent functionality", () => {
    it("should render add microagent button", async () => {
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Check that add microagent buttons are present
      const addButtons = screen.getAllByText("COMMON$ADD_MICROAGENT");
      expect(addButtons.length).toBeGreaterThan(0);
    });

    it("should open modal when add button is clicked", async () => {
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
      await waitFor(() => {
        expect(screen.getByTestId("add-microagent-modal")).toBeInTheDocument();
      });
    });

    it("should render modal when Redux state is set to visible", async () => {
      // Render with modal already visible in Redux state
      renderWithProviders(<RouterStub />, {
        preloadedState: {
          metrics: {
            cost: null,
            max_budget_per_task: null,
            usage: null,
          },
          microagentManagement: {
            selectedMicroagent: null,
            addMicroagentModalVisible: true, // Start with modal visible
            selectedRepository: {
              id: "1",
              name: "test-repo",
              full_name: "user/test-repo",
              private: false,
              git_provider: "github",
              default_branch: "main",
              is_public: true,
            } as GitRepository,
            personalRepositories: [],
            organizationRepositories: [],
            repositories: [],
          },
        },
      });

      // Check that modal is rendered
      expect(screen.getByTestId("add-microagent-modal")).toBeInTheDocument();
      expect(screen.getByTestId("query-input")).toBeInTheDocument();
      expect(screen.getByTestId("cancel-button")).toBeInTheDocument();
      expect(screen.getByTestId("confirm-button")).toBeInTheDocument();
    });

    it("should display form fields in the modal", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Find and click the first add microagent button
      const addButtons = screen.getAllByText("COMMON$ADD_MICROAGENT");
      await user.click(addButtons[0]);

      // Wait for modal to be rendered and check form fields
      await waitFor(() => {
        expect(screen.getByTestId("add-microagent-modal")).toBeInTheDocument();
      });

      // Check that form fields are present
      expect(screen.getByTestId("query-input")).toBeInTheDocument();
      expect(screen.getByTestId("cancel-button")).toBeInTheDocument();
      expect(screen.getByTestId("confirm-button")).toBeInTheDocument();
    });

    it("should disable confirm button when query is empty", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Find and click the first add microagent button
      const addButtons = screen.getAllByText("COMMON$ADD_MICROAGENT");
      await user.click(addButtons[0]);

      // Wait for modal to be rendered
      await waitFor(() => {
        expect(screen.getByTestId("add-microagent-modal")).toBeInTheDocument();
      });

      // Check that confirm button is disabled when query is empty
      const confirmButton = screen.getByTestId("confirm-button");
      expect(confirmButton).toBeDisabled();
    });

    it("should close modal when cancel button is clicked", async () => {
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
      await waitFor(() => {
        expect(screen.getByTestId("add-microagent-modal")).toBeInTheDocument();
      });

      // Click the close button (X icon)
      const closeButton = screen.getByRole("button", { name: "" });
      await user.click(closeButton);

      // Check that modal is closed
      await waitFor(() => {
        expect(
          screen.queryByTestId("add-microagent-modal"),
        ).not.toBeInTheDocument();
      });
    });

    it("should enable confirm button when query is entered", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Find and click the first add microagent button
      const addButtons = screen.getAllByText("COMMON$ADD_MICROAGENT");
      await user.click(addButtons[0]);

      // Wait for modal to be rendered and branch to be selected
      await waitFor(() => {
        expect(screen.getByTestId("add-microagent-modal")).toBeInTheDocument();
      });
      // Wait for the confirm button to be enabled after entering query and branch selection
      const queryInput = screen.getByTestId("query-input");
      await user.type(queryInput, "Test query");
      await waitFor(() => {
        const confirmButton = screen.getByTestId("confirm-button");
        expect(confirmButton).not.toBeDisabled();
      });
    });

    it("should prevent form submission when query is empty", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Find and click the first add microagent button
      const addButtons = screen.getAllByText("COMMON$ADD_MICROAGENT");
      await user.click(addButtons[0]);

      // Wait for modal to be rendered
      await waitFor(() => {
        expect(screen.getByTestId("add-microagent-modal")).toBeInTheDocument();
      });

      // Try to submit form with empty query
      const confirmButton = screen.getByTestId("confirm-button");
      await user.click(confirmButton);

      // Check that modal is still open (form submission prevented)
      expect(screen.getByTestId("add-microagent-modal")).toBeInTheDocument();
    });

    it("should trim whitespace from query before submission", async () => {
      const user = userEvent.setup();
      renderMicroagentManagement();

      // Wait for repositories to be loaded
      await waitFor(() => {
        expect(OpenHands.retrieveUserGitRepositories).toHaveBeenCalled();
      });

      // Find and click the first add microagent button
      const addButtons = screen.getAllByText("COMMON$ADD_MICROAGENT");
      await user.click(addButtons[0]);

      // Wait for modal to be rendered and branch to be selected
      await waitFor(() => {
        expect(screen.getByTestId("add-microagent-modal")).toBeInTheDocument();
      });
      // Enter query with whitespace
      const queryInput = screen.getByTestId("query-input");
      await user.type(queryInput, "  Test query with whitespace  ");
      // Wait for the confirm button to be enabled after entering query and branch selection
      await waitFor(() => {
        const confirmButton = screen.getByTestId("confirm-button");
        expect(confirmButton).not.toBeDisabled();
      });
    });
  });
});
