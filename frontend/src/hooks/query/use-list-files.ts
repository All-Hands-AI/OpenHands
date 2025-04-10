import { FileService } from "#/api/file-service/file-service.api";
import { useConversation } from "#/context/conversation-context";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { useQuery } from "@tanstack/react-query";
import { useSelector } from "react-redux";

interface UseListFilesConfig {
  path?: string;
  enabled?: boolean;
  isCached?: boolean;
}

const DEFAULT_CONFIG: UseListFilesConfig = {
  enabled: true,
  isCached: true,
};

export const useListFiles = (config: UseListFilesConfig = DEFAULT_CONFIG) => {
  const { conversationId } = useConversation();
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const runtimeIsActive = !RUNTIME_INACTIVE_STATES.includes(curAgentState);

  return useQuery({
    queryKey: ["files", conversationId, config?.path],
    queryFn: () => FileService.getFiles(conversationId, config?.path),
    enabled: runtimeIsActive && !!config?.enabled,
    staleTime: config?.isCached ? 1000 * 60 * 5 : 0, // 5 minutes
    gcTime: config?.isCached ? 1000 * 60 * 15 : 0, // 15 minutes
  });
};
