import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useConversation = (cid: string | null) =>
  useQuery({
    queryKey: ["user", "conversation", cid],
    queryFn: () => OpenHands.getConversation(cid!),
    enabled: !!cid,
    retry: false,
  });
