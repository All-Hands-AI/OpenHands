enum ActionType {
  // Initializes the agent. Only sent by client.
  INIT = "initialize",

  // Starts a new development task. Only sent by the client.
  START = "start",

  // Reads the contents of a file.
  READ = "read",

  // Writes the contents to a file.
  WRITE = "write",

  // Runs a command.
  RUN = "run",

  // Kills a background command.
  KILL = "kill",

  // Opens a web page.
  BROWSE = "browse",

  // Searches long-term memory.
  RECALL = "recall",

  // Allows the agent to make a plan, set a goal, or record thoughts.
  THINK = "think",

  // If you're absolutely certain that you've completed your task and have tested your work,
  // use the finish action to stop working.
  FINISH = "finish",
}

export default ActionType;
