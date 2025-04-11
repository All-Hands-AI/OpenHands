import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useIsAuthed } from "./use-is-authed";

export const useUserConversations = () => {
  const { data: userIsAuthenticated } = useIsAuthed();

  return useQuery({
    queryKey: ["user", "conversations"],
    queryFn: OpenHands.getUserConversations,
    enabled: !!userIsAuthenticated,
    staleTime: 1000 * 10, // 10 seconds - poll more frequently for metrics updates
    refetchInterval: 1000 * 10, // Poll every 10 seconds for metrics updates
  });
};
