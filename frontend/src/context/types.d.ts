type AgentState =
  | "init"
  | "loading"
  | "running"
  | "awaiting_user_input"
  | "finished"
  | "paused"
  | "stopped"
  | "rejected"
  | "error"
  // user states (confirmation)
  | "awaiting_user_confirmation"
  | "user_confirmed"
  | "user_rejected";
