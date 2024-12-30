import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { MULTI_CONVO_UI_IS_ENABLED } from "#/utils/constants";

export const useUserConversation = (cid: string | null) =>
  useQuery({
    queryKey: ["user", "conversation", cid],
    queryFn: () => OpenHands.getConversation(cid!),
    enabled: MULTI_CONVO_UI_IS_ENABLED && !!cid,
    retry: false,
  });
