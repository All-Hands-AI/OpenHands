import { setCurrentAgentState } from "#/state/agent-slice";
import { setUrl, setScreenshotSrc } from "#/state/browser-slice";
import store from "#/store";
import { ObservationMessage } from "#/types/message";
import { appendOutput } from "#/state/command-slice";
import { appendJupyterOutput } from "#/state/jupyter-slice";
import ObservationType from "#/types/observation-type";
import { addAssistantMessage } from "#/state/chat-slice";

export function handleObservationMessage(message: ObservationMessage) {
  switch (message.observation) {
    case ObservationType.RUN: {
      if (message.extras.hidden) break;
      let { content } = message;

      if (content.length > 5000) {
        const head = content.slice(0, 5000);
        content = `${head}\r\n\n... (truncated ${message.content.length - 5000} characters) ...`;
      }

      store.dispatch(appendOutput(content));
      break;
    }
    case ObservationType.RUN_IPYTHON:
      // FIXME: render this as markdown
      store.dispatch(appendJupyterOutput(message.content));
      break;
    case ObservationType.BROWSE:
      if (message.extras?.screenshot) {
        store.dispatch(setScreenshotSrc(message.extras?.screenshot));
      }
      if (message.extras?.url) {
        store.dispatch(setUrl(message.extras.url));
      }
      break;
    case ObservationType.AGENT_STATE_CHANGED:
      store.dispatch(setCurrentAgentState(message.extras.agent_state));
      break;
    case ObservationType.DELEGATE:
      // TODO: better UI for delegation result (#2309)
      if (message.content) {
        store.dispatch(addAssistantMessage(message.content));
      }
      break;
    default:
      store.dispatch(addAssistantMessage(message.message));
      break;
  }
}
