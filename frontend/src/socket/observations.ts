import { appendAssistantMessage } from "../state/chatSlice";
import { setUrl, setScreenshotSrc } from "../state/browserSlice";
import store from "../store";
import { ObservationMessage } from "../types/Message";

export function handleObservationMessage(message: ObservationMessage) {
  store.dispatch(appendAssistantMessage(message.message));
  if (message.observation === "browse") {
    if (message.extras?.screenshot) {
      store.dispatch(setScreenshotSrc(message.extras.screenshot));
    }
    if (message.extras?.url) {
      store.dispatch(setUrl(message.extras.url));
    }
  }
}
