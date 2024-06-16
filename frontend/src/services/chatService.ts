import ActionType from "#/types/ActionType";
import Session from "./session";

export function sendChatMessage(message: string): void {
  const event = { action: ActionType.MESSAGE, args: { content: message } };
  const eventString = JSON.stringify(event);
  Session.send(eventString);
}

export function enableAutoMode(value: boolean): void {
  const event = {
    action: ActionType.ENABLE_AUTO_MODE,
    args: { is_enabled: value },
  };
  const eventString = JSON.stringify(event);
  Session.send(eventString);
}
