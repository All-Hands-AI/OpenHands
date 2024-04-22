import { appendAssistantMessage } from "src/state/chatSlice";
import { setUrl, setScreenshotSrc } from "src/state/browserSlice";
import store from "src/store";
import { ObservationMessage } from "src/types/Message";
import { appendOutput } from "src/state/commandSlice";
import ObservationType from "src/types/ObservationType";

export function handleObservationMessage(message: ObservationMessage) {
  switch (message.observation) {
    case ObservationType.RUN:
      store.dispatch(appendOutput(message.content));
      break;
    case ObservationType.BROWSE:
      if (message.extras?.screenshot) {
        store.dispatch(setScreenshotSrc(message.extras.screenshot));
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
