import { appendAssistantMessage } from "../state/chatSlice";
import store from "../store";
import { ObservationMessage } from "./types/Message";

export function handleObservationMessage(message: ObservationMessage) {
  store.dispatch(appendAssistantMessage(message.message));
}
