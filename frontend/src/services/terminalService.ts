import ActionType from "#/types/ActionType";

export function sendTerminalCommand(command: string) {
  const event = { action: ActionType.RUN, args: { command } };
  return JSON.stringify(event);
}
