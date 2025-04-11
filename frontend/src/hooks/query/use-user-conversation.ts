import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useUserConversation = (cid: string | null) =>
  useQuery({
    queryKey: ["user", "conversation", cid],
    queryFn: () => OpenHands.getConversation(cid!),
    enabled: !!cid,
    retry: false,
    staleTime: 1000 * 10, // 10 seconds - poll more frequently for metrics updates
    gcTime: 1000 * 60 * 15, // 15 minutes
    refetchInterval: 1000 * 10, // Poll every 10 seconds for metrics updates
  });
