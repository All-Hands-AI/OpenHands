import { useMutation } from "@tanstack/react-query";
import ConversationService from "#/api/conversation-service/conversation-service.api";

export const useUploadFiles = () =>
  useMutation({
    mutationKey: ["upload-files"],
    mutationFn: (variables: { conversationId: string; files: File[] }) =>
      ConversationService.uploadFiles(
        variables.conversationId!,
        variables.files,
      ),
    onSuccess: async () => {},
    meta: {
      disableToast: true,
    },
  });
