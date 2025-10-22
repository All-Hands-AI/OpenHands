import { useMutation } from "@tanstack/react-query";
import ConversationService from "#/api/conversation-service/conversation-service.api";
import { useActiveConversation } from "../query/use-active-conversation";

export const useGetTrajectory = () => {
  const { data: conversation } = useActiveConversation();

  // TODO: Disable trajectory API call for V1 conversations
  // This is a temporary measure and may be re-enabled in the future
  const isV1Conversation = conversation?.conversation_version === "V1";

  return useMutation({
    mutationFn: (cid: string) => {
      if (isV1Conversation) {
        // Return a rejected promise for V1 conversations
        return Promise.reject(
          new Error("Trajectory API is disabled for V1 conversations"),
        );
      }
      return ConversationService.getTrajectory(cid);
    },
  });
};
