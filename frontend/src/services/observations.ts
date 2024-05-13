import { appendAssistantMessage } from "#/state/chatSlice";
import { setUrl, setScreenshotSrc } from "#/state/browserSlice";
import store from "#/store";
import { ObservationMessage } from "#/types/Message";
import { appendOutput } from "#/state/commandSlice";
import ObservationType from "#/types/ObservationType";

export function handleObservationMessage(message: ObservationMessage) {
  switch (message.observation) {
    case ObservationType.RUN:
      store.dispatch(appendOutput(message.content));
      break;
    case ObservationType.BROWSE:
      if (message.screenshot) {
        store.dispatch(setScreenshotSrc(message.screenshot));
      }
      if (message.extras?.url) {
        store.dispatch(setUrl(message.extras.url));
      }
      break;
    default:
      store.dispatch(appendAssistantMessage(message.message));
      break;
  }
}
