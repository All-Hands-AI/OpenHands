import { useQuery } from "@tanstack/react-query";
import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";
import OpenHands from "#/api/open-hands";
import { useConversation } from "#/context/conversation-context";

interface UseListFilesConfig {
  path?: string;
  enabled?: boolean;
}

const DEFAULT_CONFIG: UseListFilesConfig = {
  enabled: true,
};

export const useListFiles = (config: UseListFilesConfig = DEFAULT_CONFIG) => {
  const { conversationId } = useConversation();
  const { status } = useWsClient();
  const isActive = status === WsClientProviderStatus.CONNECTED;

  return useQuery({
    queryKey: ["files", conversationId, config?.path],
    queryFn: () => OpenHands.getFiles(conversationId, config?.path),
    enabled: !!(isActive && config?.enabled),
  });
};
