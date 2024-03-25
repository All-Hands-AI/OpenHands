import { appendUserMessage } from "../state/chatSlice";
import socket from "../state/socket";
import store from "../store";

export function sendChatMessage(message: string): void {
  store.dispatch(appendUserMessage(message));
  const event = { action: "start", args: { task: message } };
  const eventString = JSON.stringify(event);
  socket.send(eventString);
}
