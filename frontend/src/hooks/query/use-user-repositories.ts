import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useUserRepositories = () =>
  useQuery({
    queryKey: ["repositories"],
    queryFn: OpenHands.retrieveUserGitRepositories,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
