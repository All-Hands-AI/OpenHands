import ActionType from "#/types/ActionType";
import Session from "./session";

export function sendTerminalCommand(command: string): void {
  // replace END OF TEXT character
  command = command.replace(/\u0003+/, '');
  const event = { action: ActionType.RUN, args: { command } };
  const eventString = JSON.stringify(event);
  Session.send(eventString);
}
