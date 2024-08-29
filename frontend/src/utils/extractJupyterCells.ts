const isIPythonAction = (message: object): message is IPythonAction =>
  "action" in message && message.action === "run_ipython";

const isIPythonObservation = (message: object): message is IPythonObservation =>
  "observation" in message && message.observation === "run_ipython";

export const extractJupyterCells = (messages: TrajectoryItem[]) => {
  const filteredMessages = messages.filter(
    (message) => isIPythonAction(message) || isIPythonObservation(message),
  );

  return filteredMessages.map((message) => {
    if (isIPythonAction(message)) {
      return {
        type: "input",
        content:
          message.args.is_confirmed !== "rejected"
            ? message.args.code
            : "<COMMAND_REJECTED>",
      } as const;
    }

    return {
      type: "output",
      content: message.content,
    } as const;
  });
};
