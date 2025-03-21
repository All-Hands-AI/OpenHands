import { useQuery } from "@tanstack/react-query";
import { useSelector } from "react-redux";
import OpenHands from "#/api/open-hands";
import { RootState } from "#/store";

/**
 * Hook to fetch the current conversation
 *
 * @returns Query result with the conversation data
 */
export const useUserConversation = () => {
  // Get the conversation ID from the Redux store
  const conversationId = useSelector(
    (state: RootState) => state.conversation.id,
  );

  return useQuery({
    queryKey: ["user", "conversation", conversationId],
    queryFn: () => OpenHands.getConversation(conversationId!),
    enabled: !!conversationId,
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
};
