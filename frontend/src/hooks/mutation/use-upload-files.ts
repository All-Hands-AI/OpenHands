import { useMutation } from "@tanstack/react-query";
import posthog from "posthog-js";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";

type UploadFilesArgs = {
  files: File[];
};

export const useUploadFiles = () => {
  const { token } = useAuth();

  return useMutation({
    mutationFn: ({ files }: UploadFilesArgs) => {
      files.forEach(file => {
        posthog.capture("zip_file_uploaded", {
          file_name: file.name,
          file_size: file.size
        });
      });
      return OpenHands.uploadFiles(token || "", files);
    },
  });
};
