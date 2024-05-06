enum ObservationType {
  // The contents of a file
  READ = "read",

  // The HTML contents of a URL
  BROWSE = "browse",

  // The output of a command
  RUN = "run",

  // The output of an IPython command
  RUN_IPYTHON = "run_ipython",

  // The result of a search
  RECALL = "recall",

  // A message from the user
  CHAT = "chat",

  // Agent state has changed
  AGENT_STATE_CHANGED = "agent_state_changed",
}

export default ObservationType;
