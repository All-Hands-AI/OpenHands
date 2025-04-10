import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TaskSuggestions } from "#/components/features/home/tasks/task-suggestions";
import { SuggestionsService } from "#/api/suggestions-service/suggestions-service.api";
import { MOCK_TASKS } from "#/mocks/task-suggestions-handlers";

const renderTaskSuggestions = () =>
  render(<TaskSuggestions />, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={new QueryClient()}>
        {children}
      </QueryClientProvider>
    ),
  });

describe("TaskSuggestions", () => {
  const getSuggestedTasksSpy = vi.spyOn(
    SuggestionsService,
    "getSuggestedTasks",
  );

  it("should render the task suggestions section", () => {
    renderTaskSuggestions();
    screen.getByTestId("task-suggestions");
  });

  it("should render an empty message if there are no tasks", async () => {
    getSuggestedTasksSpy.mockResolvedValue([]);
    renderTaskSuggestions();
    await screen.findByText(/No tasks available/i);
  });

  it("should render the task groups with the correct titles", async () => {
    getSuggestedTasksSpy.mockResolvedValue(MOCK_TASKS);
    renderTaskSuggestions();

    await waitFor(() => {
      MOCK_TASKS.forEach((taskGroup) => {
        screen.getByText(taskGroup.title);
      });
    });
  });

  it("should render the task cards with the correct task details", async () => {
    getSuggestedTasksSpy.mockResolvedValue(MOCK_TASKS);
    renderTaskSuggestions();

    await waitFor(() => {
      MOCK_TASKS.forEach((taskGroup) => {
        taskGroup.tasks.forEach((task) => {
          screen.getByText(task.title);
          screen.getByText(task.description);
        });
      });
    });
  });
});
