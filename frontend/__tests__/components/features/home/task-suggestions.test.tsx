import { render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Provider } from "react-redux";
import { createRoutesStub } from "react-router";
import { setupStore } from "test-utils";
import { TaskSuggestions } from "#/components/features/home/tasks/task-suggestions";
import { SuggestionsService } from "#/api/suggestions-service/suggestions-service.api";
import { MOCK_TASKS } from "#/mocks/task-suggestions-handlers";
import userEvent from "@testing-library/user-event";

// Mock the translation function
vi.mock("react-i18next", async () => {
  const actual = await vi.importActual("react-i18next");
  return {
    ...(actual as object),
    useTranslation: () => ({
      t: (key: string) => key,
      i18n: {
        changeLanguage: () => new Promise(() => {}),
      },
    }),
  };
});

const renderTaskSuggestions = () => {
  const RouterStub = createRoutesStub([
    {
      Component: () => <TaskSuggestions />,
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
  ]);

  return render(<RouterStub />, {
    wrapper: ({ children }) => (
      <Provider store={setupStore()}>
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      </Provider>
    ),
  });
};

describe("TaskSuggestions", () => {
  const getSuggestedTasksSpy = vi.spyOn(
    SuggestionsService,
    "getSuggestedTasks",
  );

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render the task suggestions section", () => {
    renderTaskSuggestions();
    screen.getByTestId("task-suggestions");
  });

  it("should render an empty message if there are no tasks", async () => {
    getSuggestedTasksSpy.mockResolvedValue([]);
    renderTaskSuggestions();
    await screen.findByText("TASKS$NO_TASKS_AVAILABLE");
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
      MOCK_TASKS.forEach((task) => {
        screen.getByText(task.title);
      });
    });
  });

  it("should render skeletons when loading", async () => {
    getSuggestedTasksSpy.mockResolvedValue(MOCK_TASKS);
    renderTaskSuggestions();

    const skeletons = await screen.findAllByTestId("task-group-skeleton");
    expect(skeletons.length).toBeGreaterThan(0);

    await waitFor(() => {
      MOCK_TASKS.forEach((taskGroup) => {
        screen.getByText(taskGroup.title);
      });
    });

    expect(screen.queryByTestId("task-group-skeleton")).not.toBeInTheDocument();
  });

  it("should render the tooltip button", () => {
    renderTaskSuggestions();
    const tooltipButton = screen.getByTestId("task-suggestions-info");
    expect(tooltipButton).toBeInTheDocument();
  });

  it("should have the correct aria-label", () => {
    renderTaskSuggestions();
    const tooltipButton = screen.getByTestId("task-suggestions-info");
    expect(tooltipButton).toHaveAttribute(
      "aria-label",
      "TASKS$TASK_SUGGESTIONS_INFO",
    );
  });

  it("should render the info icon", () => {
    renderTaskSuggestions();
    const tooltipButton = screen.getByTestId("task-suggestions-info");
    const icon = tooltipButton.querySelector("svg");
    expect(icon).toBeInTheDocument();
  });
});
