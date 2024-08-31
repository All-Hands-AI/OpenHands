import { OpenHandsParsedEvent } from "#/types/core";
import { CommandAction } from "#/types/core/actions";
import { CommandObservation } from "#/types/core/observations";

const isCommandAction = (
  message: OpenHandsParsedEvent,
): message is CommandAction => "action" in message && message.action === "run";

const isCommandObservation = (
  message: OpenHandsParsedEvent,
): message is CommandObservation =>
  "observation" in message && message.observation === "run";

export interface TerminalStream {
  type: "input" | "output";
  content: string;
}

export const extractTerminalStream = (
  message: OpenHandsParsedEvent,
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
