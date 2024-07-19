import ActionType from "#/types/ActionType";
import Session from "./session";

export function sendTerminalCommand(command: string): void {
  const event = { action: ActionType.RUN, args: { command } };
  const eventString = JSON.stringify(event);
  Session.send(eventString);
}
