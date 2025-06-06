import { useQuery } from "@tanstack/react-query";
import { useConversationId } from "../use-conversation-id";
import OpenHands from "#/api/open-hands";

export const useGetMicroagentPrompt = ({ eventId }: { eventId: number }) => {
  const { conversationId } = useConversationId();

  return useQuery({
    queryKey: ["conversation", "remember_prompt", conversationId, eventId],
    queryFn: () => OpenHands.getMicroagentPrompt(conversationId, eventId),
  });
};
