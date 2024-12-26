enum ObservationType {
  // The contents of a file
  READ = "read",

  // The diff of a file edit
  EDIT = "edit",

  // The HTML contents of a URL
  BROWSE = "browse",

  // The output of a command
  RUN = "run",

  // The output of an IPython command
  RUN_IPYTHON = "run_ipython",

  // A message from the user
  CHAT = "chat",

  // Agent state has changed
  AGENT_STATE_CHANGED = "agent_state_changed",

  // Delegate result
  DELEGATE = "delegate",
}

export default ObservationType;
