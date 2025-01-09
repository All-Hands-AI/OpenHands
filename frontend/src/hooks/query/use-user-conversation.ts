import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { MULTI_CONVERSATION_UI } from "#/utils/feature-flags";

export const useUserConversation = (cid: string | null) =>
  useQuery({
    queryKey: ["user", "conversation", cid],
    queryFn: () => OpenHands.getConversation(cid!),
    enabled: MULTI_CONVERSATION_UI && !!cid,
    retry: false,
  });
