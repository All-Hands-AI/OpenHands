import { useQuery } from "@tanstack/react-query";
import { useSelector } from "react-redux";
import OpenHands from "#/api/open-hands";
import { useConversation } from "#/context/conversation-context";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";

interface UseListFilesConfig {
  path?: string;
  enabled?: boolean;
}

const DEFAULT_CONFIG: UseListFilesConfig = {
  enabled: true,
};

export const useListFiles = (config: UseListFilesConfig = DEFAULT_CONFIG) => {
  const { conversationId } = useConversation();
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const isActive = !RUNTIME_INACTIVE_STATES.includes(curAgentState);

  return useQuery({
    queryKey: ["files", conversationId, config?.path],
    queryFn: () => OpenHands.getFiles(conversationId, config?.path),
    enabled: !!(isActive && config?.enabled),
  });
};
