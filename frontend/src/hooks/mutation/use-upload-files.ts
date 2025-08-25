import { useMutation } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useUploadFiles = () =>
  useMutation({
    mutationKey: ["upload-files"],
    mutationFn: (variables: { conversationId: string; files: File[] }) =>
      OpenHands.uploadFiles(variables.conversationId!, variables.files),
    onSuccess: async () => {},
    meta: {
      disableToast: true,
    },
  });
