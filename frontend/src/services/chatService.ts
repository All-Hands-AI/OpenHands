import ActionType from "#/types/ActionType";
import Session from "./session";

export function sendChatMessage(
  message: string,
  images_base64: string[],
): void {
  const event = {
    action: ActionType.MESSAGE,
    args: { content: message, images_base64 },
  };
  const eventString = JSON.stringify(event);
  Session.send(eventString);
}
