import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";

export const useUserConversations = () => {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ["user", "conversations"],
    queryFn: OpenHands.getUserConversations,
    enabled: isAuthenticated,
    staleTime: 0,
  });
};
