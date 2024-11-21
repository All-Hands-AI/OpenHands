import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { getToken } from "#/services/auth";
import OpenHands from "#/api/open-hands";

type SaveFileArgs = {
  path: string;
  content: string;
};

export const useSaveFile = () =>
  useMutation({
    mutationFn: ({ path, content }: SaveFileArgs) =>
      OpenHands.saveFile(getToken() || "", path, content),
    onError: (error) => {
      toast.error(error.message);
    },
  });
