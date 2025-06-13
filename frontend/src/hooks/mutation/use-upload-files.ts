import { useMutation } from "@tanstack/react-query";
import { FileService } from "#/api/file-service/file-service.api";
import { FileUploadSuccessResponse } from "#/api/open-hands.types";

export const useUploadFiles = () =>
  useMutation<
    FileUploadSuccessResponse,
    Error,
    { conversationId: string; files: File[] }
  >({
    mutationKey: ["upload-files"],
    mutationFn: (variables) =>
      FileService.uploadFiles(variables.conversationId!, variables.files),
    onSuccess: async () => {},
    meta: {
      disableToast: true,
    },
  });
