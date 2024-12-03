import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import OpenHands from "#/api/open-hands";

type SaveFileArgs = {
  path: string;
  content: string;
};

export const useSaveFile = () =>
  useMutation({
    mutationFn: ({ path, content }: SaveFileArgs) =>
      OpenHands.saveFile(path, content),
    onError: (error) => {
      toast.error(error.message);
    },
  });
