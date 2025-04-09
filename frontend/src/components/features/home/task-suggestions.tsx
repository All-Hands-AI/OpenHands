import { TaskGroup } from "./task-group";
import { TaskItem } from "./task.types";

const TASKS: TaskItem[] = [
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

export function TaskSuggestions() {
  return (
    <section className="flex-1">
      <h2 className="heading">Suggested Tasks</h2>

      <div className="flex flex-col gap-6">
        <TaskGroup title="All-Hands-AI/OpenHands" tasks={TASKS} />
        <TaskGroup title="rbren/rss-parser" tasks={TASKS_2} />
        <TaskGroup title="fairwindsops/polaris" tasks={TASKS_3} />
      </div>
    </section>
  );
}
