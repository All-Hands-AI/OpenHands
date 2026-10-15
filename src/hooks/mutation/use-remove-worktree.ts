import { useMutation, useQueryClient } from "@tanstack/react-query";
import WorktreesService from "#/api/worktrees-service";
import { WORKTREES_QUERY_KEY } from "#/hooks/query/use-worktrees";

export const useRemoveWorktree = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => WorktreesService.remove(name),
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: [WORKTREES_QUERY_KEY] }),
  });
};
