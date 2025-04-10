import { http, HttpResponse } from "msw";
import {
  RepositoryTaskGroup,
  TaskItem,
} from "#/components/features/home/tasks/task.types";

const TASKS_1: TaskItem[] = [
  {
    taskId: "#6968",
    title: "Fix merge conflicts",
    description:
      "Clean up integration tests for Delegator Agent (this isn't in CI)",
  },
];

const TASKS_2: TaskItem[] = [
  {
    taskId: "#268",
    title: "Fix broken CI checks",
    description: "Fix delete text inside elements",
  },
  {
    taskId: "#281",
    title: "Fix issue",
    description: "Fix issue with the way we handle the 'on' event in the agent",
  },
  {
    taskId: "#293",
    title: "Update documentation",
    description: "Update API documentation with new endpoints and parameters",
  },
  {
    taskId: "#305",
    title: "Refactor user service",
    description:
      "Improve performance by refactoring the user authentication service",
  },
  {
    taskId: "#312",
    title: "Fix styling bug",
    description: "Fix responsive layout issues on mobile devices",
  },
  {
    taskId: "#327",
    title: "Add unit tests",
    description: "Increase test coverage for core utility functions",
  },
  {
    taskId: "#331",
    title: "Implement dark mode",
    description: "Add toggle for dark/light theme and persist user preference",
  },
  {
    taskId: "#345",
    title: "Optimize build process",
    description: "Reduce bundle size and improve build times",
  },
  {
    taskId: "#352",
    title: "Update dependencies",
    description: "Update all npm packages to latest compatible versions",
  },
];

const TASKS_3: TaskItem[] = [
  {
    taskId: "#1073",
    title: "Address PR feedback",
    description:
      "fixed pdbMinAvailableGreaterThanHPAMinReplicas and added validation for pdbMinAvailableEqualToHPAMinReplicas.",
  },
];

export const MOCK_TASKS: RepositoryTaskGroup[] = [
  { title: "octocat/hello-world", tasks: TASKS_1 },
  { title: "octocat/earth", tasks: TASKS_2 },
];

export const TASK_SUGGESTIONS_HANDLERS = [
  http.get("/api/tasks", async () => HttpResponse.json(MOCK_TASKS)),
];
