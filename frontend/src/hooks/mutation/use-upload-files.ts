import { useMutation } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";

type UploadFilesArgs = {
  files: File[];
};

export const useUploadFiles = () => {
  const { token } = useAuth();

  return useMutation({
    mutationFn: ({ files }: UploadFilesArgs) =>
      OpenHands.uploadFiles(token || "", files),
  });
};
