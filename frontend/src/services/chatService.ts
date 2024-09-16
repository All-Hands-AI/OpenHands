import ActionType from "#/types/ActionType";
import Session from "./session";

export function sendChatMessage(
  message: string,
  images_urls: string[],
  timestamp: string,
): void {
  const event = {
    action: ActionType.MESSAGE,
    args: { content: message, images_urls, timestamp },
  };
  const eventString = JSON.stringify(event);
  Session.send(eventString);
}
