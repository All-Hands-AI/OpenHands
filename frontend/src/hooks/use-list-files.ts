import { useSelector } from 'react-redux';
import { useListFilesQuery } from '../api/slices';
import { useConversation } from '../context/conversation-context';
import { RootState } from '../store';
import { RUNTIME_INACTIVE_STATES } from '../types/agent-state';

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

  return useListFilesQuery(
    { conversationId, path: config?.path },
    { skip: !(isActive && config?.enabled) }
  );
};