enum ActionType {
  // Initializes the agent. Only sent by client.
  INIT = "initialize",

  // Reconnects to the already initialized agent. Only try to reconnect.
  // If the agent is not initialized, it behaves like INIT.
  RECONNECT = "reconnect",

  // Sends a message from the user
  USER_MESSAGE = "user_message",

  // Starts a new development task
  START = "start",

  // Reads the contents of a file.
  READ = "read",

  // Writes the contents to a file.
  WRITE = "write",

  // Runs a command.
  RUN = "run",

  // Runs a IPython command.
  RUN_IPYTHON = "run_ipython",

  // Kills a background command.
  KILL = "kill",

  // Opens a web page.
  BROWSE = "browse",

  // Searches long-term memory.
  RECALL = "recall",

  // Allows the agent to make a plan, set a goal, or record thoughts.
  THINK = "think",

  // Allows the agent to respond to the user. Only sent by the agent.
  TALK = "talk",

  // If you're absolutely certain that you've completed your task and have tested your work,
  // use the finish action to stop working.
  FINISH = "finish",

  // Adds a task to the plan.
  ADD_TASK = "add_task",

  // Updates a task in the plan.
  MODIFY_TASK = "modify_task",

  CHANGE_TASK_STATE = "change_task_state",
}

export default ActionType;
