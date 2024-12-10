import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import OpenHands from "#/api/open-hands";
import { useConversation } from "#/context/conversation-context";

type SaveFileArgs = {
  path: string;
  content: string;
};

export const useSaveFile = () => {
  const { conversationId } = useConversation();
  return useMutation({
    mutationFn: ({ path, content }: SaveFileArgs) =>
      OpenHands.saveFile(conversationId, path, content),
    onError: (error) => {
      toast.error(error.message);
    },
  });
};
