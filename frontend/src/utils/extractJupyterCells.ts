const isIPythonAction = (message: object): message is IPythonAction =>
  "action" in message && message.action === "run_ipython";

const isIPythonObservation = (message: object): message is IPythonObservation =>
  "observation" in message && message.observation === "run_ipython";

export interface JupyterCell {
  type: "input" | "output";
  content: string;
}

export const extractJupyterCell = (
  message: TrajectoryItem,
): JupyterCell | null => {
  if (isIPythonAction(message)) {
    return {
      type: "input",
      content:
        message.args.is_confirmed !== "rejected"
          ? message.args.code
          : "<COMMAND_REJECTED>",
    };
  }

  if (isIPythonObservation(message)) {
    return {
      type: "output",
      content: message.content,
    };
  }

  return null;
};
