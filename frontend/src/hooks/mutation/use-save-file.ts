import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { getToken } from "#/services/auth";
import { SaveFileSuccessResponse, ErrorResponse } from "#/api/open-hands.types";

const saveFileMutationFn = async (variables: {
  path: string;
  content: string;
}) => {
  const { path, content } = variables;

  const response = await fetch("/api/save-file", {
    method: "POST",
    body: JSON.stringify({ filePath: path, content }),
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to save file");
  }

  const data = (await response.json()) as
    | SaveFileSuccessResponse
    | ErrorResponse;

  if ("error" in data) {
    throw new Error(data.error);
  }

  return data;
};

export const useSaveFile = () =>
  useMutation({
    mutationFn: saveFileMutationFn,
    onError: (error) => {
      toast.error(error.message);
    },
  });
