import { setCurrentAgentState } from "#/state/agent-slice";
import { setUrl, setScreenshotSrc } from "#/state/browser-slice";
import store from "#/store";
import { ObservationMessage } from "#/types/message";
import { AgentState } from "#/types/agent-state";
import { appendOutput } from "#/state/command-slice";
import { appendJupyterOutput } from "#/state/jupyter-slice";
import ObservationType from "#/types/observation-type";
import {
  addAssistantMessage,
  addAssistantObservation,
} from "#/state/chat-slice";

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
    case ObservationType.READ:
    case ObservationType.EDIT:
      break; // We don't display the default message for these observations
    default:
      store.dispatch(addAssistantMessage(message.message));
      break;
  }
  if (!message.extras?.hidden) {
    // Convert the message to the appropriate observation type
    const { observation } = message;
    const baseObservation = {
      ...message,
      source: "agent" as const,
    };

    switch (observation) {
      case "agent_state_changed":
        store.dispatch(
          addAssistantObservation({
            ...baseObservation,
            observation: "agent_state_changed" as const,
            extras: {
              agent_state: (message.extras.agent_state as AgentState) || "idle",
            },
          }),
        );
        break;
      case "run":
        store.dispatch(
          addAssistantObservation({
            ...baseObservation,
            observation: "run" as const,
            extras: {
              command: String(message.extras.command || ""),
              metadata: message.extras.metadata,
              hidden: Boolean(message.extras.hidden),
            },
          }),
        );
        break;
      case "read":
      case "edit":
        store.dispatch(
          addAssistantObservation({
            ...baseObservation,
            observation,
            extras: {
              path: String(message.extras.path || ""),
            },
          }),
        );
        break;
      case "run_ipython":
        store.dispatch(
          addAssistantObservation({
            ...baseObservation,
            observation: "run_ipython" as const,
            extras: {
              code: String(message.extras.code || ""),
            },
          }),
        );
        break;
      case "delegate":
        store.dispatch(
          addAssistantObservation({
            ...baseObservation,
            observation: "delegate" as const,
            extras: {
              outputs:
                typeof message.extras.outputs === "object"
                  ? (message.extras.outputs as Record<string, unknown>)
                  : {},
            },
          }),
        );
        break;
      case "browse":
        store.dispatch(
          addAssistantObservation({
            ...baseObservation,
            observation: "browse" as const,
            extras: {
              url: String(message.extras.url || ""),
              screenshot: String(message.extras.screenshot || ""),
              error: Boolean(message.extras.error),
              open_page_urls: Array.isArray(message.extras.open_page_urls)
                ? message.extras.open_page_urls
                : [],
              active_page_index: Number(message.extras.active_page_index || 0),
              dom_object:
                typeof message.extras.dom_object === "object"
                  ? (message.extras.dom_object as Record<string, unknown>)
                  : {},
              axtree_object:
                typeof message.extras.axtree_object === "object"
                  ? (message.extras.axtree_object as Record<string, unknown>)
                  : {},
              extra_element_properties:
                typeof message.extras.extra_element_properties === "object"
                  ? (message.extras.extra_element_properties as Record<
                      string,
                      unknown
                    >)
                  : {},
              last_browser_action: String(
                message.extras.last_browser_action || "",
              ),
              last_browser_action_error:
                message.extras.last_browser_action_error,
              focused_element_bid: String(
                message.extras.focused_element_bid || "",
              ),
            },
          }),
        );
        break;
      case "error":
        store.dispatch(
          addAssistantObservation({
            ...baseObservation,
            observation: "error" as const,
            source: "user" as const,
            extras: {
              error_id: message.extras.error_id,
            },
          }),
        );
        break;
      default:
        // For any unhandled observation types, just ignore them
        break;
    }
  }
}
