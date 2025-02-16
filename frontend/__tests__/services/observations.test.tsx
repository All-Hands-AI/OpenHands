import { describe, it, expect, vi, beforeEach } from 'vitest';
import { handleObservationMessage } from '../../src/services/observations';
import { AgentState } from '../../src/types/agent-state';
import { sendNotification } from '../../src/services/notification';
import store from '../../src/store';

vi.mock('../../src/services/notification');
vi.mock('../../src/store', () => ({
  default: {
    dispatch: vi.fn(),
  },
}));

describe('handleObservationMessage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should trigger notification when agent state changes to AWAITING_USER_INPUT', () => {
    const message = {
      id: 1,
      source: 'agent' as const,
      observation: 'agent_state_changed',
      extras: {
        agent_state: AgentState.AWAITING_USER_INPUT,
        metadata: {},
        error_id: '',
      },
      message: 'Agent state changed',
      content: '',
      cause: 0,
      timestamp: new Date().toISOString(),
    };

    handleObservationMessage(message);

    expect(sendNotification).toHaveBeenCalledWith('OpenHands', {
      body: 'Agent is awaiting user input...',
      icon: '/favicon.ico',
    });
  });

  it('should trigger notification when agent state changes to FINISHED', () => {
    const message = {
      id: 2,
      source: 'agent' as const,
      observation: 'agent_state_changed',
      extras: {
        agent_state: AgentState.FINISHED,
        metadata: {},
        error_id: '',
      },
      message: 'Agent state changed',
      content: '',
      cause: 0,
      timestamp: new Date().toISOString(),
    };

    handleObservationMessage(message);

    expect(sendNotification).toHaveBeenCalledWith('OpenHands', {
      body: 'Task completed successfully!',
      icon: '/favicon.ico',
    });
  });

  it('should not trigger notification for other agent states', () => {
    const message = {
      id: 3,
      source: 'agent' as const,
      observation: 'agent_state_changed',
      extras: {
        agent_state: AgentState.RUNNING,
        metadata: {},
        error_id: '',
      },
      message: 'Agent state changed',
      content: '',
      cause: 0,
      timestamp: new Date().toISOString(),
    };

    handleObservationMessage(message);

    expect(sendNotification).not.toHaveBeenCalled();
  });
});