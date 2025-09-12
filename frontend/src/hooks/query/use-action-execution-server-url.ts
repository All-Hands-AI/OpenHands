import { useQuery } from "@tanstack/react-query";
import { useSelector } from "react-redux";
import { openHands } from "#/api/open-hands-axios";
import { RootState } from "#/store";
import { useConversationId } from "#/hooks/use-conversation-id";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";

interface ActionExecutionServerInfo {
  url: string;
  session_api_key: string | null;
}

export const useActionExecutionServerUrl = () => {
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const { conversationId } = useConversationId();

  const { data } = useQuery({
    queryKey: ["conversation", "action_execution_server", conversationId],
    queryFn: async () => {
      const response = await openHands.get<ActionExecutionServerInfo>(
        `/api/conversations/${conversationId}/action-execution-server-url`,
      );
      return {
        url: response.data.url,
        sessionApiKey: response.data.session_api_key,
      };
    },
    enabled: !RUNTIME_INACTIVE_STATES.includes(curAgentState),
    initialData: { url: "", sessionApiKey: null },
  });

  return { url: data.url, sessionApiKey: data.sessionApiKey };
};
