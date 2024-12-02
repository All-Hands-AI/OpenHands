import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

interface UseListFileConfig {
  path: string;
}

export const useListFile = (config: UseListFileConfig) =>
  useQuery({
    queryKey: ["file", config.path],
    queryFn: () => OpenHands.getFile(config.path),
    enabled: false, // don't fetch by default, trigger manually via `refetch`
  });
