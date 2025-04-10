import OpenHands from "#/api/open-hands";
import { useQuery } from "@tanstack/react-query";
import { useLocation } from "react-router";

export const useUserConversation = (cid: string | null, isPublic?: boolean | null) => {
  const location = useLocation()
  const { pathname } = location || {}
  const isShared = pathname.includes("shares")

  return useQuery({
    queryKey: ["user", "conversation", cid],
    queryFn: () => OpenHands.getConversation(cid!, isShared),
    enabled: !!cid,
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
}
