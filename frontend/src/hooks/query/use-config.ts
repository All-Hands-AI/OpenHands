import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useConfig = () => {
  const query = useQuery({
    queryKey: ["config"],
    queryFn: OpenHands.getConfig,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });

  // Store config in global variable when it's available
  if (query.data && typeof window !== 'undefined') {
    window.__OPENHANDS_CONFIG__ = query.data;
  }

  return query;
};
