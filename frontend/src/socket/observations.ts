import { appendAssistantMessage } from "../state/chatSlice";
import store from "../store";
import { ObservationMessage } from "../types/Message";
import { appendOutput } from "../state/commandSlice";
import ObservationType from "../types/ObservationType";

export function handleObservationMessage(message: ObservationMessage) {
  switch (message.observation) {
    case ObservationType.RUN:
      store.dispatch(appendOutput(message.content));
      break;
    default:
      store.dispatch(appendAssistantMessage(message.message));
      break;
  }
}
