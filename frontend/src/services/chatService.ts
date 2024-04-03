import { appendUserMessage } from "../state/chatSlice";
import Socket from "../socket/socket";
import store from "../store";
import { SocketMessage } from "../types/ResponseType";
import { ActionMessage } from "../types/Message";

export function sendChatMessage(message: string): void {
  store.dispatch(appendUserMessage(message));
  const event = { action: "start", args: { task: message } };
  const eventString = JSON.stringify(event);
  Socket.send(eventString);
}

export function sendChatMessageFromEvent(event: string | SocketMessage): void {
  try {
    let data: ActionMessage;
    if (typeof event === "string") {
      data = JSON.parse(event);
    } else {
      data = event as ActionMessage;
    }
    if (data && data.args && data.args.task) {
      store.dispatch(appendUserMessage(data.args.task));
    }
  } catch (error) {
    //
  }
}
