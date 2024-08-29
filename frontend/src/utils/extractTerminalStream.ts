const isCommandAction = (message: object): message is CommandAction =>
  "action" in message && message.action === "run";

const isCommandObservation = (message: object): message is CommandObservation =>
  "observation" in message && message.observation === "run";

export interface TerminalStream {
  type: "input" | "output";
  content: string;
}

export const extractTerminalStream = (
  message: TrajectoryItem,
): TerminalStream | null => {
  if (isCommandAction(message)) {
    return {
      type: "input",
      content:
        message.args.is_confirmed !== "rejected"
          ? message.args.command
          : "<COMMAND_REJECTED>",
    };
  }

  if (isCommandObservation(message)) {
    return {
      type: "input",
      content: message.content,
    };
  }

  return null;
};
