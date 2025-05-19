import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useUserConversation = (cid: string | null) =>
  useQuery({
    queryKey: ["user", "conversation", cid],
    queryFn: async () => {
      const conversation = await OpenHands.getConversation(cid!);
      OpenHands.setCurrentConversation(conversation);
      return conversation;
    },
    enabled: !!cid,
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
