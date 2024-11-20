import { useMutation } from "@tanstack/react-query";
import { getToken } from "#/services/auth";
import {
  FileUploadSuccessResponse,
  ErrorResponse,
} from "#/api/open-hands.types";

const uploadFilesMutationFn = async (variables: { files: File[] }) => {
  const formData = new FormData();
  variables.files.forEach((file) => formData.append("files", file));

  const response = await fetch("/api/upload-files", {
    method: "POST",
    body: formData,
    headers: {
      Authorization: `Bearer ${getToken()}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to upload files");
  }

  const data = (await response.json()) as
    | FileUploadSuccessResponse
    | ErrorResponse;

  if ("error" in data) {
    throw new Error(data.error);
  }

  return data;
};

export const useUploadFiles = () =>
  useMutation({
    mutationFn: uploadFilesMutationFn,
  });
