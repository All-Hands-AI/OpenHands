import { useQuery } from "@tanstack/react-query";
import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";
import OpenHands from "#/api/open-hands";
import { useConversation } from "#/context/conversation-context";
import { useAuth } from "#/context/auth-context";

interface UseListFilesConfig {
  path?: string;
  enabled?: boolean;
}

export const useListFiles = (config?: UseListFilesConfig) => {
  const { token } = useAuth();
  const { conversationId } = useConversation();
  const { status } = useWsClient();
  const isActive = status === WsClientProviderStatus.ACTIVE;

  return useQuery({
    queryKey: ["files", token, conversationId, config?.path],
    queryFn: () => OpenHands.getFiles(conversationId, config?.path),
    enabled: !!(isActive && config?.enabled && token),
  });
};
