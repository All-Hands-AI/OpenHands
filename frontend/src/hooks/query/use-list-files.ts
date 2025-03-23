import { useQuery } from "@tanstack/react-query";
import { useSelector } from "react-redux";
import OpenHands from "#/api/open-hands";
import { useConversation } from "#/context/conversation-context";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { QueryKeys } from "#/utils/query/query-keys";
import { useFileStateContext } from "#/context/file-state-context";

interface UseListFilesConfig {
  path?: string;
  enabled?: boolean;
}

const DEFAULT_CONFIG: UseListFilesConfig = {
  enabled: true,
};

/**
 * Hook to list files in a conversation
 * Uses React Query for data fetching and caching
 */
export const useListFiles = (config: UseListFilesConfig = DEFAULT_CONFIG) => {
  const { conversationId } = useConversation();
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const { fileStates } = useFileStateContext();
  const isActive = !RUNTIME_INACTIVE_STATES.includes(curAgentState);

  // Get files from the API
  const query = useQuery({
    queryKey: QueryKeys.files(conversationId, config?.path),
    queryFn: () => OpenHands.getFiles(conversationId, config?.path),
    enabled: !!(isActive && config?.enabled && conversationId),
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });

  // Enhance the result with file state information
  const enhancedData = query.data?.map(filePath => {
    const fileState = fileStates.find(state => state.path === filePath);
    return {
      path: filePath,
      changed: fileState?.changed || false
    };
  });

  return {
    ...query,
    enhancedData
  };
};
