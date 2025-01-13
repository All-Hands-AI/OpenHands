import { useEffect, useRef } from 'react';
import { ProjectStatus } from '../components/features/conversation-panel/conversation-state-indicator';
import { sendNotification } from '../services/notification';

export const useAgentStatusNotification = (status: ProjectStatus) => {
  const previousStatus = useRef<ProjectStatus>(status);

  useEffect(() => {
    if (previousStatus.current === 'RUNNING' && status === 'STOPPED') {
      sendNotification('OpenHands Agent', {
        body: 'The agent has finished its task',
        icon: '/android-chrome-192x192.png'
      });
    }
    previousStatus.current = status;
  }, [status]);
};
