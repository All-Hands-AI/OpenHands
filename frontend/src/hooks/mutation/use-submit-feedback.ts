import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { Feedback } from "#/api/open-hands.types";
import OpenHands from "#/api/open-hands";
import { useConversation } from "#/context/conversation-context";

type SubmitFeedbackArgs = {
  feedback: Feedback;
};

export const useSubmitFeedback = () => {
  const { conversationId } = useConversation();
  return useMutation({
    mutationFn: ({ feedback }: SubmitFeedbackArgs) =>
      OpenHands.submitFeedback(conversationId, feedback),
    onError: (error) => {
      toast.error(error.message);
    },
  });
};
