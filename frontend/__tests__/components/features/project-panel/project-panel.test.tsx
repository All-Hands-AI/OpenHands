import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { ProjectPanel } from "#/components/features/project-panel/project-panel";

describe("ProjectPanel", () => {
  it.todo("should render a loading indicator when fetching projects");

  it("should render the projects", async () => {
    render(<ProjectPanel />, {
      wrapper: ({ children }) => (
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      ),
    });
    const cards = await screen.findAllByTestId("project-card");

    expect(cards).toHaveLength(3);
  });

  it("should cancel deleting a project", async () => {
    const user = userEvent.setup();
    render(<ProjectPanel />, {
      wrapper: ({ children }) => (
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      ),
    });
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
    render(<ProjectPanel />, {
      wrapper: ({ children }) => (
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      ),
    });
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

  it.todo("should rename a project");
});
