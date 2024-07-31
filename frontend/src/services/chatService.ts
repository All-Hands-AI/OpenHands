import ActionType from "#/types/ActionType";
import Session from "./session";

export function sendChatMessage(message: string, images_urls: string[]): void {
  const event = {
    action: ActionType.MESSAGE,
    args: { content: message, images_urls },
  };
  const eventString = JSON.stringify(event);
  Session.send(eventString);
}
