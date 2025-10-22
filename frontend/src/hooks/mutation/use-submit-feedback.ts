import { useMutation } from "@tanstack/react-query";
import { Feedback } from "#/api/open-hands.types";
import ConversationService from "#/api/conversation-service/conversation-service.api";
import { useConversationId } from "#/hooks/use-conversation-id";
import { useActiveConversation } from "../query/use-active-conversation";
import { displayErrorToast } from "#/utils/custom-toast-handlers";

type SubmitFeedbackArgs = {
  feedback: Feedback;
};

export const useSubmitFeedback = () => {
  const { conversationId } = useConversationId();
  const { data: conversation } = useActiveConversation();

  // TODO: Disable feedback API call for V1 conversations
  // This is a temporary measure and may be re-enabled in the future
  const isV1Conversation = conversation?.conversation_version === "V1";

  return useMutation({
    mutationFn: ({ feedback }: SubmitFeedbackArgs) => {
      if (isV1Conversation) {
        // Return a rejected promise for V1 conversations
        return Promise.reject(
          new Error("Feedback API is disabled for V1 conversations"),
        );
      }
      return ConversationService.submitFeedback(conversationId, feedback);
    },
    onError: (error) => {
      displayErrorToast(error.message);
    },
    retry: 2,
    retryDelay: 500,
  });
};
