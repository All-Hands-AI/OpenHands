import { expect, test } from "vitest";
import {
  SuggestedTask,
  SuggestedTaskGroup,
} from "#/components/features/home/tasks/task.types";
import { groupSuggestedTasks } from "#/utils/group-suggested-tasks";

const rawTasks: SuggestedTask[] = [
  {
    id: 1,
    repo: "repo1",
    title: "Task 1",
    type: "MERGE_CONFLICTS",
  },
  {
    id: 2,
    repo: "repo1",
    title: "Task 2",
    type: "FAILING_CHECKS",
  },
  {
    id: 3,
    repo: "repo2",
    title: "Task 3",
    type: "UNRESOLVED_COMMENTS",
  },
  {
    id: 4,
    repo: "repo2",
    title: "Task 4",
    type: "OPEN_ISSUE",
  },
  {
    id: 5,
    repo: "repo3",
    title: "Task 5",
    type: "OPEN_PR",
  },
];

const groupedTasks: SuggestedTaskGroup[] = [
  {
    title: "repo1",
    tasks: [
      {
        id: 1,
        repo: "repo1",
        title: "Task 1",
        type: "MERGE_CONFLICTS",
      },
      {
        id: 2,
        repo: "repo1",
        title: "Task 2",
        type: "FAILING_CHECKS",
      },
    ],
  },
  {
    title: "repo2",
    tasks: [
      {
        id: 3,
        repo: "repo2",
        title: "Task 3",
        type: "UNRESOLVED_COMMENTS",
      },
      {
        id: 4,
        repo: "repo2",
        title: "Task 4",
        type: "OPEN_ISSUE",
      },
    ],
  },
  {
    title: "repo3",
    tasks: [
      {
        id: 5,
        repo: "repo3",
        title: "Task 5",
        type: "OPEN_PR",
      },
    ],
  },
];

test("groupSuggestedTasks", () => {
  expect(groupSuggestedTasks(rawTasks)).toEqual(groupedTasks);
});
