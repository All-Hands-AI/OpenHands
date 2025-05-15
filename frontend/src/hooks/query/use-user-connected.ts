import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

/**
 * Hook to check if a user is connected to any provider (including local git provider)
 * This is determined by whether the /api/user/info endpoint returns a 200 status code
 */
export const useUserConnected = () => {
  return useQuery({
    queryKey: ["user-connected"],
    queryFn: async () => {
      try {
        await OpenHands.getGitUser();
        return true;
      } catch (error) {
        return false;
      }
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
};