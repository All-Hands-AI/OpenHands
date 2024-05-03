import store from "#/store";
import ActionType from "#/types/ActionType";
import { SocketMessage } from "#/types/ResponseType";
import { ActionMessage } from "#/types/Message";
import Socket from "./socket";
import { addUserMessage } from "#/state/chatSlice";

export function sendChatMessage(message: string, isTask: boolean = true): void {
  store.dispatch(addUserMessage(message));
  let event;
  if (isTask) {
    event = { action: ActionType.START, args: { task: message } };
  } else {
    event = { action: ActionType.USER_MESSAGE, args: { message } };
  }
  const eventString = JSON.stringify(event);
  Socket.send(eventString);
}

export function addChatMessageFromEvent(event: string | SocketMessage): void {
  try {
    let data: ActionMessage;
    if (typeof event === "string") {
      data = JSON.parse(event);
    } else {
      data = event as ActionMessage;
    }
    if (data && data.args && data.args.task) {
      store.dispatch(addUserMessage(data.args.task));
    }
  } catch (error) {
    //
  }
}
