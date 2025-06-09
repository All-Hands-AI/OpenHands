import { useMutation } from "@tanstack/react-query";
import { FileService } from "#/api/file-service/file-service.api";

export const useUploadFiles = () =>
  useMutation<string[], Error, { conversationId: string; files: File[] }>({
    mutationKey: ["upload-files"],
    mutationFn: (variables) =>
      FileService.uploadFiles(variables.conversationId!, variables.files),
    onSuccess: async () => {},
    meta: {
      disableToast: true,
    },
  });
