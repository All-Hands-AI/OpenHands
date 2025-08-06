import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useIsAuthed } from "./use-is-authed";

export const useUserConversations = (limit: number = 20) => {
  const { data: userIsAuthenticated } = useIsAuthed();

  return useQuery({
    queryKey: ["user", "conversations", limit],
    queryFn: async () => {
      const result = await OpenHands.getUserConversations(limit);
      return result.results; // Return just the conversations array for backward compatibility
    },
    enabled: !!userIsAuthenticated,
  });
};
