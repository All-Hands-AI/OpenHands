import {
  Message,
  appeendToNewChatSequence,
  appendUserMessage,
  emptyOutQueuedTyping,
  setCurrentQueueMarker,
  setCurrentTypingMessage,
  toggleTypingActive,
} from "../state/chatSlice";
import socket from "../socket/socket";
import store from "../store";

export function sendChatMessage(message: string): void {
  store.dispatch(appendUserMessage(message));
  const event = { action: "start", args: { task: message } };
  const eventString = JSON.stringify(event);
  socket.send(eventString);
}

export function setTypingAcitve(bool: boolean): void {
  store.dispatch(toggleTypingActive(bool));
}

export function resetQueuedTyping(): void {
  store.dispatch(emptyOutQueuedTyping());
}

export function setCurrentTypingMsgState(msg: string): void {
  store.dispatch(setCurrentTypingMessage(msg));
}
export function setCurrentQueueMarkerState(index: number): void {
  store.dispatch(setCurrentQueueMarker(index));
}
export function addAssistanctMessageToChat(msg: Message): void {
  store.dispatch(appeendToNewChatSequence(msg));
}
