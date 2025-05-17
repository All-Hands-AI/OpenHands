import { useMutation } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useSummarizeConversation = () =>
  useMutation({
    mutationFn: (cid: string) => OpenHands.summarizeConversation(cid),
  });
