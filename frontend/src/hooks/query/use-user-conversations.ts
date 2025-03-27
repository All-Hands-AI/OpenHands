import { useQuery } from "@tanstack/react-query";
import { useIsAuthed } from "./use-is-authed";
import { ConversationService } from "#/api/conversation-service/conversation-service.api";

export const useUserConversations = () => {
  const { data: userIsAuthenticated } = useIsAuthed();

  return useQuery({
    queryKey: ["user", "conversations"],
    queryFn: ConversationService.getConversations,
    enabled: !!userIsAuthenticated,
  });
};
