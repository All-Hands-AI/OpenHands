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
  { title: "All-Hands-AI/OpenHands", tasks: TASKS_1 },
  { title: "rbren/rss-parser", tasks: TASKS_2 },
  { title: "fairwindsops/polaris", tasks: TASKS_3 },
];

export const TASK_SUGGESTIONS_HANDLERS = [
  http.get("/api/tasks", async () => HttpResponse.json(MOCK_TASKS)),
];
