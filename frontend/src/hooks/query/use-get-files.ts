import { useQuery } from "@tanstack/react-query";
import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";
import OpenHands from "#/api/open-hands";

interface UseListFilesConfig {
  token: string | null;
  path?: string;
  enabled?: boolean;
}

export const useGetFiles = (config: UseListFilesConfig) => {
  const { status } = useWsClient();
  const isActive = status === WsClientProviderStatus.ACTIVE;

  return useQuery({
    queryKey: ["files", config.token, config.path],
    queryFn: () => OpenHands.getFiles(config.token!, config.path),
    enabled: isActive && config.enabled && !!config.token,
  });
};
