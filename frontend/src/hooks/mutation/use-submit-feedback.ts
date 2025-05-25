import { useMutation } from "@tanstack/react-query";
import { Feedback } from "#/api/open-hands.types";
import OpenHands from "#/api/open-hands";
import { useConversationId } from "#/hooks/use-conversation-id";
import { displayErrorToast } from "#/utils/custom-toast-handlers";

type SubmitFeedbackArgs = {
  feedback: Feedback;
};

export const useSubmitFeedback = () => {
  const { conversationId } = useConversationId();
  return useMutation({
    mutationFn: async ({ feedback }: SubmitFeedbackArgs) => {
      // 添加重试逻辑
      const maxRetries = 2;
      let retryCount = 0;
      let lastError;

      while (retryCount < maxRetries) {
        try {
          return await OpenHands.submitFeedback(conversationId, feedback);
        } catch (error) {
          lastError = error;
          retryCount++;
          // 如果不是最后一次尝试，不显示错误提示
          if (retryCount < maxRetries) {
            // 等待短暂时间后重试
            await new Promise(resolve => setTimeout(resolve, 500));
          }
        }
      }
      // 所有重试都失败后抛出最后的错误
      throw lastError;
    },
    onError: (error) => {
      displayErrorToast(error.message);
    },
  });
};
