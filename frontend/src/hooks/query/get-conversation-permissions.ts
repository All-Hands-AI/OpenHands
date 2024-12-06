import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useConversationPermissions = (cid: string | null) =>
  useQuery({
    queryKey: ["user", "conversation", "permissions", cid],
    queryFn: () => OpenHands.getConversationPermissions(cid!),
    enabled: !!cid,
    retry: false,
  });
