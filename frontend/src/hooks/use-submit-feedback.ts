import { useSubmitFeedbackMutation } from "../api/slices";
import { useConversation } from "../context/conversation-context";
import { Feedback } from "../api/open-hands.types";

export const useSubmitFeedback = () => {
  const { conversationId } = useConversation();
  const [submitFeedbackMutation] = useSubmitFeedbackMutation();

  const submitFeedback = (feedback: Feedback) =>
    submitFeedbackMutation({ conversationId, feedback });

  return { submitFeedback };
};
