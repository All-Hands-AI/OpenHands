import { useQuery } from "@tanstack/react-query";
import { useSelector } from "react-redux";
import { useConversation } from "#/context/conversation-context";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { FileService } from "#/api/file-service/file-service.api";

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
  const runtimeIsActive = !RUNTIME_INACTIVE_STATES.includes(curAgentState);

  return useQuery({
    queryKey: ["files", conversationId, config?.path],
    queryFn: () => FileService.getFiles(conversationId, config?.path),
    enabled: runtimeIsActive && !!config?.enabled,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
};
