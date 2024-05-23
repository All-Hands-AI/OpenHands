import ActionType from "#/types/ActionType";
import Session from "./session";

export function sendChatMessage(message: string): void {
  const event = { action: ActionType.MESSAGE, args: { content: message } };
  const eventString = JSON.stringify(event);
  Session.send(eventString);
}
