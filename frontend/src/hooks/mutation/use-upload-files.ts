import { useMutation } from "@tanstack/react-query";
import { getToken } from "#/services/auth";
import OpenHands from "#/api/open-hands";

type UploadFilesArgs = {
  files: File[];
};

export const useUploadFiles = () =>
  useMutation({
    mutationFn: ({ files }: UploadFilesArgs) =>
      OpenHands.uploadFiles(getToken() || "", files),
  });
