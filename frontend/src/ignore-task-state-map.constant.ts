import { AgentState } from "./types/agent-state";

export const IGNORE_TASK_STATE_MAP: Record<string, AgentState[]> = {
  [AgentState.PAUSED]: [
    AgentState.INIT,
    AgentState.PAUSED,
    AgentState.STOPPED,
    AgentState.FINISHED,
    AgentState.REJECTED,
    AgentState.AWAITING_USER_INPUT,
    AgentState.AWAITING_USER_CONFIRMATION,
  ],
  [AgentState.RUNNING]: [
    AgentState.INIT,
    AgentState.RUNNING,
    AgentState.STOPPED,
    AgentState.FINISHED,
    AgentState.REJECTED,
    AgentState.AWAITING_USER_INPUT,
    AgentState.AWAITING_USER_CONFIRMATION,
  ],
  [AgentState.STOPPED]: [AgentState.INIT, AgentState.STOPPED],
  [AgentState.USER_CONFIRMED]: [AgentState.RUNNING],
  [AgentState.USER_REJECTED]: [AgentState.RUNNING],
  [AgentState.AWAITING_USER_CONFIRMATION]: [],
};
