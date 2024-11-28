import { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '#/store';
import AgentState from '#/types/agent-state';
import { useUserPrefs } from '#/context/user-prefs-context';

export function useCloseWarning() {
  const [showWarning, setShowWarning] = useState(false);
  const { settings } = useUserPrefs();
  const agentState = useSelector((state: RootState) => state.agent.curAgentState);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      const isWorking = agentState === AgentState.RUNNING || agentState === AgentState.STARTING;
      
      if (settings.CLOSE_WARNING === 'always' || 
          (settings.CLOSE_WARNING === 'while_working' && isWorking)) {
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [agentState, settings.CLOSE_WARNING]);

  return {
    showWarning,
    setShowWarning,
  };
}
