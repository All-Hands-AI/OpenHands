import { render, screen, within } from "@testing-library/react";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import {
  QueryClientProvider,
  QueryClient,
  QueryClientConfig,
} from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { ProjectPanel } from "#/components/features/project-panel/project-panel";
import OpenHands from "#/api/open-hands";
import { AuthProvider } from "#/context/auth-context";

describe("ProjectPanel", () => {
  const onCloseMock = vi.fn();

  const renderProjectPanel = (config?: QueryClientConfig) =>
    render(<ProjectPanel onClose={onCloseMock} />, {
      wrapper: ({ children }) => (
        <AuthProvider>
          <QueryClientProvider client={new QueryClient(config)}>
            {children}
          </QueryClientProvider>
        </AuthProvider>
      ),
    });

  const { endSessionMock, searchParamsGetMock } = vi.hoisted(() => ({
    endSessionMock: vi.fn(),
    searchParamsGetMock: vi.fn(),
  }));

  beforeAll(() => {
    vi.mock("react-router", async (importOriginal) => ({
      ...(await importOriginal<typeof import("react-router")>()),
      Link: ({ children }: React.PropsWithChildren) => children,
      useNavigate: vi.fn(() => vi.fn()),
      useLocation: vi.fn(() => ({ pathname: "/conversation" })),
      useSearchParams: vi.fn(() => [{ get: searchParamsGetMock }]),
    }));

    vi.mock("#/hooks/use-end-session", async (importOriginal) => ({
      ...(await importOriginal<typeof import("#/hooks/use-end-session")>()),
      useEndSession: vi.fn(() => endSessionMock),
    }));
  });

  beforeEach(() => {
    vi.clearAllMocks();
    vi.restoreAllMocks();
  });

  it.todo("should render a loading indicator when fetching projects");

  it("should render the projects", async () => {
    renderProjectPanel();
    const cards = await screen.findAllByTestId("project-card");

    expect(cards).toHaveLength(3);
  });

  it("should display an empty state when there are no projects", async () => {
    const getUserProjectsSpy = vi.spyOn(OpenHands, "getUserProjects");
    getUserProjectsSpy.mockResolvedValue([]);

    renderProjectPanel();

    const emptyState = await screen.findByText("No projects found");
    expect(emptyState).toBeInTheDocument();
  });

  it("should handle an error when fetching projects", async () => {
    const getUserProjectsSpy = vi.spyOn(OpenHands, "getUserProjects");
    getUserProjectsSpy.mockRejectedValue(new Error("Failed to fetch projects"));

    renderProjectPanel({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    const error = await screen.findByText("Failed to fetch projects");
    expect(error).toBeInTheDocument();
  });

  it("should cancel deleting a project", async () => {
    const user = userEvent.setup();
    renderProjectPanel();

    let cards = await screen.findAllByTestId("project-card");
    expect(
      within(cards[0]).queryByTestId("delete-button"),
    ).not.toBeInTheDocument();

    const ellipsisButton = within(cards[0]).getByTestId("ellipsis-button");
    await user.click(ellipsisButton);
    const deleteButton = screen.getByTestId("delete-button");

    // Click the first delete button
    await user.click(deleteButton);

    // Cancel the deletion
    const cancelButton = screen.getByText("Cancel");
    await user.click(cancelButton);

    expect(screen.queryByText("Cancel")).not.toBeInTheDocument();

    // Ensure the project is not deleted
    cards = await screen.findAllByTestId("project-card");
    expect(cards).toHaveLength(3);
  });

  it("should call endSession after deleting a project that is the current session", async () => {
    searchParamsGetMock.mockReturnValue("2"); // id of the second project
    const user = userEvent.setup();
    renderProjectPanel();

    let cards = await screen.findAllByTestId("project-card");
    const ellipsisButton = within(cards[1]).getByTestId("ellipsis-button");
    await user.click(ellipsisButton);
    const deleteButton = screen.getByTestId("delete-button");

    // Click the second delete button
    await user.click(deleteButton);

    // Confirm the deletion
    const confirmButton = screen.getByText("Confirm");
    await user.click(confirmButton);

    expect(screen.queryByText("Confirm")).not.toBeInTheDocument();

    // Ensure the project is deleted
    cards = await screen.findAllByTestId("project-card");
    expect(cards).toHaveLength(2);

    expect(endSessionMock).toHaveBeenCalledOnce();
  });

  it("should delete a project", async () => {
    const user = userEvent.setup();
    renderProjectPanel();

    let cards = await screen.findAllByTestId("project-card");
    const ellipsisButton = within(cards[0]).getByTestId("ellipsis-button");
    await user.click(ellipsisButton);
    const deleteButton = screen.getByTestId("delete-button");

    // Click the first delete button
    await user.click(deleteButton);

    // Confirm the deletion
    const confirmButton = screen.getByText("Confirm");
    await user.click(confirmButton);

    expect(screen.queryByText("Confirm")).not.toBeInTheDocument();

    // Ensure the project is deleted
    cards = await screen.findAllByTestId("project-card");
    expect(cards).toHaveLength(1);
  });

  it("should rename a project", async () => {
    const updateUserProjectSpy = vi.spyOn(OpenHands, "updateUserProject");

    const user = userEvent.setup();
    renderProjectPanel();
    const cards = await screen.findAllByTestId("project-card");
    const title = within(cards[0]).getByTestId("project-card-title");

    await user.clear(title);
    await user.type(title, "Project 1 Renamed");
    await user.tab();

    // Ensure the project is renamed
    expect(updateUserProjectSpy).toHaveBeenCalledWith("3", {
      name: "Project 1 Renamed",
    });
  });

  it("should not rename a project when the name is unchanged", async () => {
    const updateUserProjectSpy = vi.spyOn(OpenHands, "updateUserProject");

    const user = userEvent.setup();
    renderProjectPanel();
    const cards = await screen.findAllByTestId("project-card");
    const title = within(cards[0]).getByTestId("project-card-title");

    await user.click(title);
    await user.tab();

    // Ensure the project is not renamed
    expect(updateUserProjectSpy).not.toHaveBeenCalled();

    await user.type(title, "Project 1");
    await user.click(title);
    await user.tab();

    expect(updateUserProjectSpy).toHaveBeenCalledTimes(1);

    await user.click(title);
    await user.tab();

    expect(updateUserProjectSpy).toHaveBeenCalledTimes(1);
  });

  it("should call onClose after clicking a card", async () => {
    renderProjectPanel();
    const cards = await screen.findAllByTestId("project-card");
    const firstCard = cards[0];

    await userEvent.click(firstCard);

    expect(onCloseMock).toHaveBeenCalledOnce();
  });

  describe("New Project Button", () => {
    it("should display a confirmation modal when clicking", async () => {
      const user = userEvent.setup();
      renderProjectPanel();

      expect(
        screen.queryByTestId("confirm-new-project-modal"),
      ).not.toBeInTheDocument();

      const newProjectButton = screen.getByTestId("new-project-button");
      await user.click(newProjectButton);

      const modal = screen.getByTestId("confirm-new-project-modal");
      expect(modal).toBeInTheDocument();
    });

    it("should call endSession and close panel after confirming", async () => {
      const user = userEvent.setup();
      renderProjectPanel();

      const newProjectButton = screen.getByTestId("new-project-button");
      await user.click(newProjectButton);

      const confirmButton = screen.getByText("Confirm");
      await user.click(confirmButton);

      expect(endSessionMock).toHaveBeenCalledOnce();
      expect(onCloseMock).toHaveBeenCalledOnce();
    });

    it("should close the modal when cancelling", async () => {
      const user = userEvent.setup();
      renderProjectPanel();

      const newProjectButton = screen.getByTestId("new-project-button");
      await user.click(newProjectButton);

      const cancelButton = screen.getByText("Cancel");
      await user.click(cancelButton);

      expect(endSessionMock).not.toHaveBeenCalled();
      expect(
        screen.queryByTestId("confirm-new-project-modal"),
      ).not.toBeInTheDocument();
    });
  });
});
