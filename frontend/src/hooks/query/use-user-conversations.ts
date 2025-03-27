import { useQuery } from "@tanstack/react-query";
import { useIsAuthed } from "./use-is-authed";
import { conversationService } from "#/api/conversation-service/conversation-service.api";

export const useUserConversations = () => {
  const { data: userIsAuthenticated } = useIsAuthed();

  return useQuery({
    queryKey: ["user", "conversations"],
    queryFn: conversationService.getConversations,
    enabled: !!userIsAuthenticated,
  });
};
