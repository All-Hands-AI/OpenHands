import { render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, test, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { formatTimeDelta } from "#/utils/format-time-delta";
import { ProjectCard } from "#/components/features/project-panel/project-card";

describe("ProjectCard", () => {
  const onClick = vi.fn();
  const onDelete = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render the project card", () => {
    render(
      <ProjectCard
        onDelete={onDelete}
        onClick={onClick}
        name="Project 1"
        lastUpdated="2021-10-01T12:00:00Z"
      />,
    );
    const expectedDate = `${formatTimeDelta(new Date("2021-10-01T12:00:00Z"))} ago`;

    const card = screen.getByTestId("project-card");
    within(card).getByText("Project 1");
    within(card).getByText(expectedDate);
  });

  it("should render the repo if available", () => {
    const { rerender } = render(
      <ProjectCard
        onDelete={onDelete}
        onClick={onClick}
        name="Project 1"
        lastUpdated="2021-10-01T12:00:00Z"
      />,
    );

    expect(screen.queryByTestId("project-card-repo")).not.toBeInTheDocument();

    rerender(
      <ProjectCard
        onDelete={onDelete}
        onClick={onClick}
        name="Project 1"
        repo="org/repo"
        lastUpdated="2021-10-01T12:00:00Z"
      />,
    );

    screen.getByTestId("project-card-repo");
  });

  it("should call onClick when the card is clicked", async () => {
    const user = userEvent.setup();
    render(
      <ProjectCard
        onDelete={onDelete}
        onClick={onClick}
        name="Project 1"
        lastUpdated="2021-10-01T12:00:00Z"
      />,
    );

    const card = screen.getByTestId("project-card");
    await user.click(card);

    expect(onClick).toHaveBeenCalled();
  });

  it("should call onDelete when the delete button is clicked", async () => {
    const user = userEvent.setup();
    render(
      <ProjectCard
        onClick={onClick}
        onDelete={onDelete}
        name="Project 1"
        lastUpdated="2021-10-01T12:00:00Z"
      />,
    );

    const deleteButton = screen.getByTestId("delete-button");
    await user.click(deleteButton);

    expect(onDelete).toHaveBeenCalled();
  });

  test("clicking the repo should not trigger the onClick handler", async () => {
    const user = userEvent.setup();
    render(
      <ProjectCard
        onClick={onClick}
        onDelete={onDelete}
        name="Project 1"
        repo="org/repo"
        lastUpdated="2021-10-01T12:00:00Z"
      />,
    );

    const repo = screen.getByTestId("project-card-repo");
    await user.click(repo);

    expect(onClick).not.toHaveBeenCalled();
  });

  describe("state indicator", () => {
    it("should render the 'cold' indicator by default", () => {
      render(
        <ProjectCard
          onClick={onClick}
          onDelete={onDelete}
          name="Project 1"
          lastUpdated="2021-10-01T12:00:00Z"
        />,
      );

      screen.getByTestId("cold-indicator");
    });

    it("should render the other indicators when provided", () => {
      render(
        <ProjectCard
          onClick={onClick}
          onDelete={onDelete}
          name="Project 1"
          lastUpdated="2021-10-01T12:00:00Z"
          state="warm"
        />,
      );

      expect(screen.queryByTestId("cold-indicator")).not.toBeInTheDocument();
      screen.getByTestId("warm-indicator");
    });
  });
});
