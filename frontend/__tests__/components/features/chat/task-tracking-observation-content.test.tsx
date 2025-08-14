import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { TaskTrackingObservationContent } from "#/components/features/chat/task-tracking-observation-content";
import { TaskTrackingObservation } from "#/types/core/observations";

// Mock the translation hook
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "TASK_TRACKING_OBSERVATION$COMMAND": "Command",
        "TASK_TRACKING_OBSERVATION$TASK_LIST": "Task List",
        "TASK_TRACKING_OBSERVATION$TASK_ID": "ID",
        "TASK_TRACKING_OBSERVATION$TASK_NOTES": "Notes",
        "TASK_TRACKING_OBSERVATION$RESULT": "Result",
      };
      return translations[key] || key;
    },
  }),
}));

describe("TaskTrackingObservationContent", () => {
  const mockEvent: TaskTrackingObservation = {
    id: 123,
    timestamp: "2024-01-01T00:00:00Z",
    source: "agent",
    observation: "task_tracking",
    content: "Task tracking operation completed successfully",
    cause: 122,
    message: "Task tracking operation completed successfully",
    extras: {
      command: "plan",
      task_list: [
        {
          id: "task-1",
          title: "Implement feature A",
          status: "todo",
          notes: "This is a test task",
        },
        {
          id: "task-2",
          title: "Fix bug B",
          status: "in_progress",
        },
        {
          id: "task-3",
          title: "Deploy to production",
          status: "done",
          notes: "Completed successfully",
        },
      ],
    },
  };

  it("renders command section", () => {
    render(<TaskTrackingObservationContent event={mockEvent} />);

    expect(screen.getByText("Command")).toBeInTheDocument();
    expect(screen.getByText("plan")).toBeInTheDocument();
  });

  it("renders task list when command is 'plan' and tasks exist", () => {
    render(<TaskTrackingObservationContent event={mockEvent} />);

    expect(screen.getByText("Task List (3 items)")).toBeInTheDocument();
    expect(screen.getByText("Implement feature A")).toBeInTheDocument();
    expect(screen.getByText("Fix bug B")).toBeInTheDocument();
    expect(screen.getByText("Deploy to production")).toBeInTheDocument();
  });

  it("displays correct status icons and badges", () => {
    render(<TaskTrackingObservationContent event={mockEvent} />);

    // Check for status text (the icons are emojis)
    expect(screen.getByText("todo")).toBeInTheDocument();
    expect(screen.getByText("in progress")).toBeInTheDocument();
    expect(screen.getByText("done")).toBeInTheDocument();
  });

  it("displays task IDs and notes", () => {
    render(<TaskTrackingObservationContent event={mockEvent} />);

    expect(screen.getByText("ID: task-1")).toBeInTheDocument();
    expect(screen.getByText("ID: task-2")).toBeInTheDocument();
    expect(screen.getByText("ID: task-3")).toBeInTheDocument();

    expect(screen.getByText("Notes: This is a test task")).toBeInTheDocument();
    expect(screen.getByText("Notes: Completed successfully")).toBeInTheDocument();
  });

  it("renders result section when content exists", () => {
    render(<TaskTrackingObservationContent event={mockEvent} />);

    expect(screen.getByText("Result")).toBeInTheDocument();
    expect(screen.getByText("Task tracking operation completed successfully")).toBeInTheDocument();
  });

  it("does not render task list when command is not 'plan'", () => {
    const eventWithoutPlan = {
      ...mockEvent,
      extras: {
        ...mockEvent.extras,
        command: "view",
      },
    };

    render(<TaskTrackingObservationContent event={eventWithoutPlan} />);

    expect(screen.getByText("Command")).toBeInTheDocument();
    expect(screen.getByText("view")).toBeInTheDocument();
    expect(screen.queryByText("Task List")).not.toBeInTheDocument();
  });

  it("does not render task list when task list is empty", () => {
    const eventWithEmptyTasks = {
      ...mockEvent,
      extras: {
        ...mockEvent.extras,
        task_list: [],
      },
    };

    render(<TaskTrackingObservationContent event={eventWithEmptyTasks} />);

    expect(screen.queryByText("Task List")).not.toBeInTheDocument();
  });

  it("does not render result section when content is empty", () => {
    const eventWithoutContent = {
      ...mockEvent,
      content: "",
    };

    render(<TaskTrackingObservationContent event={eventWithoutContent} />);

    expect(screen.queryByText("Result")).not.toBeInTheDocument();
  });
});
