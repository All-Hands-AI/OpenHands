enum ObservationType {
  // The contents of a file
  READ = "read",

  // The HTML contents of a URL
  BROWSE = "browse",

  // The output of a command
  RUN = "run",

  // The result of a search
  RECALL = "recall",

  // A message from the user
  CHAT = "chat",
}

export default ObservationType;
