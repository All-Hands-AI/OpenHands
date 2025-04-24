import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useUserConversation = (cid: string | null) =>
  useQuery({
    queryKey: ["user", "conversation", cid],
    queryFn: () => OpenHands.getConversation(cid!),
    enabled: !!cid,
    retry: false,
    staleTime: 1000 * 30, // 30 seconds - reduced from 5 minutes for more responsive title updates
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
