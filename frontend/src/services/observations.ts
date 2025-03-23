import {
  setUrl,
  setScreenshotSrc,
} from "#/services/context-services/browser-service";
import { ObservationMessage } from "#/types/message";
import { AgentState } from "#/types/agent-state";
import { appendOutput } from "#/services/context-services/terminal-service";
// Import from context service instead of Redux slice
import { appendJupyterOutput } from "#/services/context-services/jupyter-service";
import { updateAgentState } from "#/services/context-services/agent-state-service";
import ObservationType from "#/types/observation-type";
// Import will be restored when observation handling is implemented
// import { addAssistantObservation } from "#/services/context-services/chat-service";

export function handleObservation(message: ObservationMessage) {
  switch (message.type) {
    case ObservationType.TERMINAL_OUTPUT: {
      let { content } = message;

      if (content.length > 5000) {
        const head = content.slice(0, 5000);
        content = `${head}\r\n\n... (truncated ${message.content.length - 5000} characters) ...`;
      }

      appendOutput(content);
      break;
    }
    case ObservationType.RUN_IPYTHON:
      // FIXME: render this as markdown
      appendJupyterOutput(message.content);
      break;
    case ObservationType.BROWSE:
      if (message.extras?.screenshot) {
        setScreenshotSrc(message.extras?.screenshot as string);
      }
      if (message.extras?.url) {
        setUrl(message.extras.url as string);
      }
      break;
    case ObservationType.AGENT_STATE_CHANGED:
      // Cast to AgentState since we know it's a valid agent state
      updateAgentState(message.extras.agent_state as AgentState);
      break;
    case ObservationType.OBSERVATION:
      // Skip complex observation handling for now
      // This will be fixed in a future PR
      break;
    default:
      // Unknown message type
      break;
  }
}
