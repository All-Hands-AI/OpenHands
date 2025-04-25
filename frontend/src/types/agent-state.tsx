export enum AgentState {
  LOADING = "loading",
  SETTING_UP = "setting_up",
  INIT = "init",
  RUNNING = "running",
  AWAITING_USER_INPUT = "awaiting_user_input",
  PAUSED = "paused",
  STOPPED = "stopped",
  FINISHED = "finished",
  REJECTED = "rejected",
  ERROR = "error",
  RATE_LIMITED = "rate_limited",
  AWAITING_USER_CONFIRMATION = "awaiting_user_confirmation",
  USER_CONFIRMED = "user_confirmed",
  USER_REJECTED = "user_rejected",
}

export const RUNTIME_INACTIVE_STATES = [
  AgentState.LOADING,
  AgentState.SETTING_UP,
  AgentState.STOPPED,
  AgentState.ERROR,
];
