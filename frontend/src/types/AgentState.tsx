enum AgentState {
  LOADING = "loading",
  INIT = "init",
  RUNNING = "running",
  AWAITING_USER_INPUT = "awaiting_user_input",
  PAUSED = "paused",
  STOPPED = "stopped",
  FINISHED = "finished",
  REJECTED = "rejected",
  ERROR = "error",
  AWAITING_USER_CONFIRMATION = "awaiting_user_confirmation",
  ACTION_CONFIRMED = "action_confirmed",
  ACTION_REJECTED = "action_rejected",
}

export default AgentState;
