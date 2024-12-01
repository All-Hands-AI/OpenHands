import { useQuery } from "@tanstack/react-query";
import React from "react";
import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";
import OpenHands from "#/api/open-hands";

export const useConversationConfig = () => {
  const { status } = useWsClient();

  const query = useQuery({
    queryKey: ["conversation_config"],
    queryFn: OpenHands.getRuntimeId,
    enabled: status === WsClientProviderStatus.ACTIVE,
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
