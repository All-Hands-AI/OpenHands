import {
  SuggestedTask,
  SuggestedTaskGroup,
} from "#/components/features/home/tasks/task.types";

/**
 * Groups suggested tasks by their repository.
 * @param tasks Array of suggested tasks
 * @returns Array of suggested task groups
 */
export function groupSuggestedTasks(
  tasks: SuggestedTask[],
): SuggestedTaskGroup[] {
  const groupsMap: Record<string, SuggestedTaskGroup> = {};

  for (const task of tasks) {
    if (!groupsMap[task.repo]) {
      groupsMap[task.repo] = {
        title: task.repo,
        tasks: [],
      };
    }

    groupsMap[task.repo].tasks.push(task);
  }

  return Object.values(groupsMap);
}
