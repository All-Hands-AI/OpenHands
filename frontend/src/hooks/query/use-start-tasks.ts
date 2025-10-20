import { useQuery } from "@tanstack/react-query";
import V1ConversationService from "#/api/conversation-service/v1-conversation-service.api";

/**
 * Hook to fetch in-progress V1 conversation start tasks
 *
 * Use case: Show tasks that are provisioning sandboxes, cloning repos, etc.
 * These are conversations that started but haven't reached READY or ERROR status yet.
 *
 * Note: Filters out READY and ERROR status tasks client-side since backend doesn't support status filtering.
 *
 * @param limit Maximum number of tasks to return (max 100)
 * @returns Query result with array of in-progress start tasks
 */
export const useStartTasks = (limit = 10) =>
  useQuery({
    queryKey: ["start-tasks", "search", limit],
    queryFn: () => V1ConversationService.searchStartTasks(limit),
    select: (tasks) =>
      tasks.filter(
        (task) => task.status !== "READY" && task.status !== "ERROR",
      ),
    staleTime: 1000 * 60 * 1, // 1 minute (short since these are in-progress)
    gcTime: 1000 * 60 * 5, // 5 minutes
  });
