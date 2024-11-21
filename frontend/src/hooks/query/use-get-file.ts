import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";

interface UseGetFileConfig {
  path: string;
}

export const useGetFile = (config: UseGetFileConfig) => {
  const { token } = useAuth();

  return useQuery({
    queryKey: ["file", token, config.path],
    queryFn: () => OpenHands.getFile(token || "", config.path),
    enabled: false, // don't fetch by default, trigger manually via `refetch`
  });
};
