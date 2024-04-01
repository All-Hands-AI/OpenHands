import { appendUserMessage } from "../state/chatSlice";
import socket from "../socket/socket";
import store from "../store";
import ActionType from "../types/ActionType";

export function sendChatMessage(message: string): void {
  store.dispatch(appendUserMessage(message));
  const event = { action: ActionType.START, args: { task: message } };
  const eventString = JSON.stringify(event);
  socket.send(eventString);
}
