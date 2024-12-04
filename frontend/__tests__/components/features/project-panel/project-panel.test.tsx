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

describe("ProjectPanel", () => {
  const onCloseMock = vi.fn();

  const renderProjectPanel = (config?: QueryClientConfig) =>
    render(<ProjectPanel onClose={onCloseMock} />, {
      wrapper: ({ children }) => (
        <QueryClientProvider client={new QueryClient(config)}>
          {children}
        </QueryClientProvider>
      ),
    });

  beforeAll(() => {
    vi.mock("react-router", async (importOriginal) => ({
      ...(await importOriginal<typeof import("react-router")>()),
      Link: ({ children }: React.PropsWithChildren) => children,
      useNavigate: () => vi.fn(),
    }));
  });

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it.todo("should render a loading indicator when fetching projects");

  it("should render the projects", async () => {
    renderProjectPanel();
    const cards = await screen.findAllByTestId("project-card");

    expect(cards).toHaveLength(3);
  });

  it("should be able to refresh the projects", async () => {
    const user = userEvent.setup();
    const getUserProjectsSpy = vi.spyOn(OpenHands, "getUserProjects");

    renderProjectPanel();
    expect(getUserProjectsSpy).toHaveBeenCalledTimes(1);
    const refreshButton = await screen.findByTestId("refresh-button");

    await user.click(refreshButton);
    expect(getUserProjectsSpy).toHaveBeenCalledTimes(2);
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
    const firstDeleteButton = within(cards[0]).getByTestId("delete-button");

    // Click the first delete button
    await user.click(firstDeleteButton);

    // Cancel the deletion
    const cancelButton = screen.getByText("Cancel");
    await user.click(cancelButton);

    expect(screen.queryByText("Cancel")).not.toBeInTheDocument();

    // Ensure the project is not deleted
    cards = await screen.findAllByTestId("project-card");
    expect(cards).toHaveLength(3);
  });

  it("should delete a project", async () => {
    const user = userEvent.setup();
    renderProjectPanel();
    let cards = await screen.findAllByTestId("project-card");
    const firstDeleteButton = within(cards[0]).getByTestId("delete-button");

    // Click the first delete button
    await user.click(firstDeleteButton);

    // Confirm the deletion
    const confirmButton = screen.getByText("Confirm");
    await user.click(confirmButton);

    expect(screen.queryByText("Confirm")).not.toBeInTheDocument();

    // Ensure the project is deleted
    cards = await screen.findAllByTestId("project-card");
    expect(cards).toHaveLength(2);
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
    expect(updateUserProjectSpy).toHaveBeenCalledWith("2", {
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
});
