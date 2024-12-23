import { useQuery } from "@tanstack/react-query";
import React from "react";
import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";
import { useConversation } from "#/context/conversation-context";
import OpenHands from "#/api/open-hands";

export const useConversationConfig = () => {
  const { status } = useWsClient();
  const { conversationId } = useConversation();

  const query = useQuery({
    queryKey: ["conversation_config", conversationId],
    queryFn: () => {
      if (!conversationId) throw new Error("No conversation ID");
      return OpenHands.getRuntimeId(conversationId);
    },
    enabled: status === WsClientProviderStatus.CONNECTED && !!conversationId,
  });

  React.useEffect(() => {
    if (query.data) {
      const { runtime_id: runtimeId } = query.data;

      // eslint-disable-next-line no-console
      console.log(
        "Runtime ID: %c%s",
        "background: #444; color: #ffeb3b; font-weight: bold; padding: 2px 4px; border-radius: 4px;",
        runtimeId,
      );
    }
  }, [query.data]);

  return query;
};
