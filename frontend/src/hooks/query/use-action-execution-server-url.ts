import { useQuery } from "@tanstack/react-query";
import { useSelector } from "react-redux";
import { openHands } from "#/api/open-hands-axios";
import { RootState } from "#/store";
import { useConversation } from "#/context/conversation-context";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";

export const useActionExecutionServerUrl = () => {
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const { conversationId } = useConversation();

  const { data } = useQuery({
    queryKey: [conversationId, "url"],
    queryFn: async () => {
      const response = await openHands.get<{ url: string }>(
        `/api/conversations/${conversationId}/action-execution-server-url`,
      );
      return { url: response.data.url };
    },
    enabled: !RUNTIME_INACTIVE_STATES.includes(curAgentState),
    initialData: { url: "" },
  });

  return { url: data.url };
};
