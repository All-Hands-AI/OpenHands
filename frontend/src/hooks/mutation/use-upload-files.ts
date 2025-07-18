import { useMutation } from "@tanstack/react-query";
import { FileService } from "#/api/file-service/file-service.api";

export const useUploadFiles = () =>
  useMutation({
    mutationKey: ["upload-files"],
    mutationFn: (variables: { conversationId: string; files: File[] }) =>
      FileService.uploadFiles(variables.conversationId!, variables.files),
    onSuccess: async () => {},
    meta: {
      disableToast: true,
    },
  });
