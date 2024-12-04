import { useQuery } from "@tanstack/react-query";
import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";

interface UseListFilesConfig {
  path?: string;
  enabled?: boolean;
}

export const useListFiles = (config?: UseListFilesConfig) => {
  const { token } = useAuth();
  const { status } = useWsClient();
  const isActive = status === WsClientProviderStatus.ACTIVE;

  return useQuery({
    queryKey: ["files", token, config?.path],
    queryFn: () => OpenHands.getFiles(config?.path),
    enabled: !!(isActive && config?.enabled && token),
  });
};
