import { changeAgentState } from "#/state/agentSlice";
import { setUrl, setScreenshotSrc } from "#/state/browserSlice";
import store from "#/store";
import { ObservationMessage } from "#/types/Message";
import { appendOutput } from "#/state/commandSlice";
import { appendJupyterOutput } from "#/state/jupyterSlice";
import ObservationType from "#/types/ObservationType";
import { addAssistantMessage } from "#/state/chatSlice";

export function handleObservationMessage(message: ObservationMessage) {
  switch (message.observation) {
    case ObservationType.RUN:
      store.dispatch(appendOutput(message.content));
      break;
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
      store.dispatch(changeAgentState(message.extras.agent_state));
      break;
    default:
      store.dispatch(addAssistantMessage(message.message));
      break;
  }
}
