import { useMutation } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useConversationContext } from "#/context/conversation-context";

type UploadFilesArgs = {
  files: File[];
};

export const useUploadFiles = () => {
  const { conversationId } = useConversationContext();

  return useMutation({
    mutationFn: ({ files }: UploadFilesArgs) =>
      OpenHands.uploadFiles(conversationId, files),
  });
};
