import { useQuery } from "@tanstack/react-query";
import React from "react";
import { useConversationId } from "#/hooks/use-conversation-id";
import OpenHands from "#/api/open-hands";
import { useRuntimeIsReady } from "../use-runtime-is-ready";

export const useConversationConfig = () => {
  const { conversationId } = useConversationId();
  const runtimeIsReady = useRuntimeIsReady();

  const query = useQuery({
    queryKey: ["conversation_config", conversationId],
    queryFn: () => {
      if (!conversationId) throw new Error("No conversation ID");
      return OpenHands.getRuntimeId(conversationId);
    },
    enabled: runtimeIsReady && !!conversationId,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
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
