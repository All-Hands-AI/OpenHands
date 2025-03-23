import { setUrl, setScreenshotSrc } from "#/services/context-services/browser-service";
import { ObservationMessage } from "#/types/message";
import { AgentState } from "#/types/agent-state";
import { appendOutput } from "#/services/context-services/terminal-service";
import { appendJupyterOutput } from "#/state/jupyter-slice";
import { updateAgentState } from "#/services/context-services/agent-state-service";
import ObservationType from "#/types/observation-type";
import {
  addAssistantObservation,
} from "#/services/context-services/chat-service";

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
      {
        // Base observation object
        const baseObservation = {
          id: message.id,
          timestamp: message.timestamp,
        };

      // Handle different observation types
      switch (message.extras.observation_type) {
        case "agent_state":
          addAssistantObservation({
            ...baseObservation,
            observation: "agent_state" as const,
            extras: {
              agent_state: (message.extras.agent_state as AgentState) || "idle",
            },
          });
          break;
        case "run":
          addAssistantObservation({
            ...baseObservation,
            observation: "run" as const,
            extras: {
              command: String(message.extras.command || ""),
              metadata: message.extras.metadata,
              hidden: Boolean(message.extras.hidden),
            },
          });
          break;
        case "function_call":
          addAssistantObservation({
            ...baseObservation,
            observation: "function_call" as const,
            extras: {
              name: String(message.extras.name || ""),
              args: message.extras.args,
              impl_source: String(message.extras.impl_source || ""),
            },
          });
          break;
        case "file_edit":
          addAssistantObservation({
            ...baseObservation,
            observation: "file_edit" as const,
            extras: {
              path: String(message.extras.path || ""),
              diff: String(message.extras.diff || ""),
              impl_source: String(message.extras.impl_source || ""),
            },
          });
          break;
        case "file_read":
          addAssistantObservation({
            ...baseObservation,
            observation: "file_read" as const,
            extras: {
              path: String(message.extras.path || ""),
              content: String(message.extras.content || ""),
            },
          });
          break;
        case "browser":
          addAssistantObservation({
            ...baseObservation,
            observation: "browser" as const,
            extras: {
              url: String(message.extras.url || ""),
              title: String(message.extras.title || ""),
              screenshot: String(message.extras.screenshot || ""),
              error: Boolean(message.extras.error),
              open_page_urls: Array.isArray(message.extras.open_page_urls)
                ? message.extras.open_page_urls
                : [],
              active_page_index: Number(message.extras.active_page_index || 0),
              dom_object:
                typeof message.extras.dom_object === "object"
                  ? message.extras.dom_object
                  : {},
              axtree_object:
                typeof message.extras.axtree_object === "object"
                  ? message.extras.axtree_object
                  : {},
              extra_element_properties:
                typeof message.extras.extra_element_properties === "object"
                  ? message.extras.extra_element_properties
                  : {},
              last_browser_action: String(
                message.extras.last_browser_action || ""
              ),
              last_browser_action_error:
                message.extras.last_browser_action_error || null,
              focused_element_bid: String(
                message.extras.focused_element_bid || ""
              ),
            },
          });
          break;
        case "web_search":
          addAssistantObservation({
            ...baseObservation,
            observation: "web_search" as const,
            extras: {
              query: String(message.extras.query || ""),
              results: Array.isArray(message.extras.results)
                ? message.extras.results
                : [],
            },
          });
          break;
        default:
          // Unknown observation type
      }
      }
      break;
    default:
      // Unknown message type
      break;
  }
}