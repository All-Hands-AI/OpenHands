import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TaskCard } from "#/components/features/home/tasks/task-card";
import { SuggestedTask } from "#/components/features/home/tasks/task.types";

describe("TaskCard", () => {
  const MOCK_TASK: SuggestedTask = {
    issue_number: 123,
    repo: "repo1",
    title: "Task 1",
    task_type: "MERGE_CONFLICTS",
  };

  it("format the issue id", async () => {
    render(<TaskCard task={MOCK_TASK} />);

    const taskId = screen.getByTestId("task-id");
    expect(taskId).toHaveTextContent(/#123/i);
  });
});
