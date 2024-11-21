import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

interface UseGetFileConfig {
  token: string | null;
  path: string;
}

export const useGetFile = (config: UseGetFileConfig) =>
  useQuery({
    queryKey: ["file", config.token, config.path],
    queryFn: () => OpenHands.getFile(config.token || "", config.path),
    enabled: false, // don't fetch by default, trigger manually via `refetch`
  });
