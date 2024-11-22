import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";

type SaveFileArgs = {
  path: string;
  content: string;
};

export const useSaveFile = () => {
  const { token } = useAuth();

  return useMutation({
    mutationFn: ({ path, content }: SaveFileArgs) =>
      OpenHands.saveFile(token || "", path, content),
    onError: (error) => {
      toast.error(error.message);
    },
  });
};
