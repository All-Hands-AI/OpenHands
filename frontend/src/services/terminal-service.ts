import ActionType from "#/types/action-type";

export function getTerminalCommand(command: string, hidden: boolean = false) {
  const event = { action: ActionType.RUN, args: { command, hidden } };
  return event;
}

export function getStopProcessesCommand() {
  const event = { action: ActionType.RUN, args: { command: "pkill -P $$" } };
  return event;
}
