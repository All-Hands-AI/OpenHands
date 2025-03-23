import { useSelector } from 'react-redux';
import { useGetFileQuery } from '../api/slices';
import { useConversation } from '../context/conversation-context';
import { RootState } from '../store';
import { RUNTIME_INACTIVE_STATES } from '../types/agent-state';

interface UseListFileConfig {
  path: string;
  enabled?: boolean;
}

const DEFAULT_CONFIG: Omit<UseListFileConfig, 'path'> = {
  enabled: true,
};

export const useListFile = ({ path, enabled = DEFAULT_CONFIG.enabled }: UseListFileConfig) => {
  const { conversationId } = useConversation();
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const isActive = !RUNTIME_INACTIVE_STATES.includes(curAgentState);

  return useGetFileQuery(
    { conversationId, path },
    { skip: !(isActive && enabled) }
  );
};