import store from "#/store";
import ActionType from "#/types/ActionType";
import { SocketMessage } from "#/types/ResponseType";
import { ActionMessage } from "#/types/Message";
import Session from "./session";
import { addUserMessage } from "#/state/chatSlice";

export function sendChatMessage(message: string): void {
  const event = { action: ActionType.MESSAGE, args: { content: message } };
  const eventString = JSON.stringify(event);
  Session.send(eventString);
}
