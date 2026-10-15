import { useQuery } from "@tanstack/react-query";
import WorktreesService from "#/api/worktrees-service";
import { useActiveBackend } from "#/contexts/active-backend-context";

export const WORKTREES_QUERY_KEY = "worktrees";

/** Conversation worktrees of the active local backend, for cleanup. */
export function useWorktrees() {
  const { backend } = useActiveBackend();
  return useQuery({
    queryKey: [WORKTREES_QUERY_KEY, backend.id, backend.host],
    queryFn: () => WorktreesService.list(),
    enabled: backend.kind === "local",
    retry: false,
    // An agent-server without the endpoint just shows no list.
    meta: { disableToast: true },
  });
}
