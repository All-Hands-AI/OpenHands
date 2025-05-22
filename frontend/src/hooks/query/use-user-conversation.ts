import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

const FIVE_MINUTES = 1000 * 60 * 5;
const FIFTEEN_MINUTES = 1000 * 60 * 15;

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
    refetchInterval: (query) => {
      if (query.state.data?.status === "STARTING") {
        return 2000; // 2 seconds
      }
      return FIVE_MINUTES;
    },
    staleTime: FIVE_MINUTES,
    gcTime: FIFTEEN_MINUTES,
  });
