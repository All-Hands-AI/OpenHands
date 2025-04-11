import { http, HttpResponse } from "msw";
import { SuggestedTask } from "#/components/features/home/tasks/task.types";

const TASKS_1: SuggestedTask[] = [
  {
    id: 6968,
    title: "Fix merge conflicts",
    repo: "octocat/hello-world",
    type: "MERGE_CONFLICTS",
  },
];

const TASKS_2: SuggestedTask[] = [
  {
    id: 268,
    title: "Fix broken CI checks",
    repo: "octocat/earth",
    type: "FAILING_CHECKS",
  },
  {
    id: 281,
    title: "Fix issue",
    repo: "octocat/earth",
    type: "UNRESOLVED_COMMENTS",
  },
  {
    id: 293,
    title: "Update documentation",
    repo: "octocat/earth",
    type: "OPEN_ISSUE",
  },
  {
    id: 305,
    title: "Refactor user service",
    repo: "octocat/earth",
    type: "OPEN_PR",
  },
  {
    id: 312,
    title: "Fix styling bug",
    repo: "octocat/earth",
    type: "OPEN_PR",
  },
  {
    id: 327,
    title: "Add unit tests",
    repo: "octocat/earth",
    type: "OPEN_PR",
  },
  {
    id: 331,
    title: "Implement dark mode",
    repo: "octocat/earth",
    type: "OPEN_PR",
  },
  {
    id: 345,
    title: "Optimize build process",
    repo: "octocat/earth",
    type: "OPEN_PR",
  },
  {
    id: 352,
    title: "Update dependencies",
    repo: "octocat/earth",
    type: "OPEN_PR",
  },
];

export const MOCK_TASKS = [...TASKS_1, ...TASKS_2];

export const TASK_SUGGESTIONS_HANDLERS = [
  http.get("/api/tasks", async () => HttpResponse.json(MOCK_TASKS)),
];
