import { ObservationMessage } from "#/types/message";
import { queryClient } from "#/entry.client";
import { chatKeys } from "#/hooks/query/use-chat";
import { setCurrentAgentState } from "#/state/agent-slice";
import { setUrl, setScreenshotSrc } from "#/state/browser-slice";
import store from "#/store";
import { AgentState } from "#/types/agent-state";
import { appendOutput } from "#/state/command-slice";
import { appendJupyterOutput } from "#/state/jupyter-slice";
import ObservationType from "#/types/observation-type";

// Helper function to get chat functions
const getChatFunctions = () => {
  // Get the current chat state
  const currentState = queryClient.getQueryData(chatKeys.messages()) || {
    messages: [],
  };

  const addAssistantMessage = (content: string) => {
    const newState = { ...currentState };

    const message = {
      type: "thought",
      sender: "assistant",
      content,
      imageUrls: [],
      timestamp: new Date().toISOString(),
      pending: false,
    };

    newState.messages.push(message);
    queryClient.setQueryData(chatKeys.messages(), newState);
  };

  const addAssistantObservation = (observation: Record<string, unknown>) => {
    const newState = { ...currentState };

    // Find the cause message and update it
    const observationID = observation.observation;
    const causeID = observation.cause;
    const causeMessage = newState.messages.find(
      (message: Record<string, unknown>) => message.eventID === causeID,
    );

    if (causeMessage) {
      causeMessage.translationID = `OBSERVATION_MESSAGE$${observationID.toUpperCase()}`;

      // Set success property based on observation type
      if (observationID === "run") {
        causeMessage.success = observation.extras.metadata.exit_code === 0;
      } else if (observationID === "run_ipython") {
        causeMessage.success = !observation.content
          .toLowerCase()
          .includes("error:");
      } else if (observationID === "read" || observationID === "edit") {
        if (observation.extras.impl_source === "oh_aci") {
          causeMessage.success =
            observation.content.length > 0 &&
            !observation.content.startsWith("ERROR:\n");
        } else {
          causeMessage.success =
            observation.content.length > 0 &&
            !observation.content.toLowerCase().includes("error:");
        }
      }

      // Update content based on observation type
      if (observationID === "run" || observationID === "run_ipython") {
        let { content } = observation;
        if (content.length > 1000) {
          content = `${content.slice(0, 1000)}...`;
        }
        content = `${
          causeMessage.content
        }\n\nOutput:\n\`\`\`\n${content.trim() || "[Command finished execution with no output]"}\n\`\`\``;
        causeMessage.content = content;
      } else if (observationID === "read") {
        causeMessage.content = `\`\`\`\n${observation.content}\n\`\`\``;
      } else if (observationID === "edit") {
        if (causeMessage.success) {
          causeMessage.content = `\`\`\`diff\n${observation.extras.diff}\n\`\`\``;
        } else {
          causeMessage.content = observation.content;
        }
      } else if (observationID === "browse") {
        let content = `**URL:** ${observation.extras.url}\n`;
        if (observation.extras.error) {
          content += `**Error:**\n${observation.extras.error}\n`;
        }
        content += `**Output:**\n${observation.content}`;
        if (content.length > 1000) {
          content = `${content.slice(0, 1000)}...`;
        }
        causeMessage.content = content;
      }

      queryClient.setQueryData(chatKeys.messages(), newState);
    }
  };

  return {
    addAssistantMessage,
    addAssistantObservation,
  };
};

export function handleObservationMessage(message: ObservationMessage) {
  const chatFunctions = getChatFunctions();

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
      if (message.content && chatFunctions) {
        chatFunctions.addAssistantMessage(message.content);
      }
      break;
    case ObservationType.READ:
    case ObservationType.EDIT:
    case ObservationType.THINK:
    case ObservationType.NULL:
      break; // We don't display the default message for these observations
    default:
      if (chatFunctions) {
        chatFunctions.addAssistantMessage(message.message);
      }
      break;
  }

  if (!message.extras?.hidden && chatFunctions) {
    // Convert the message to the appropriate observation type
    const { observation } = message;
    const baseObservation = {
      ...message,
      source: "agent" as const,
    };

    switch (observation) {
      case "agent_state_changed":
        chatFunctions.addAssistantObservation({
          ...baseObservation,
          observation: "agent_state_changed" as const,
          extras: {
            agent_state: (message.extras.agent_state as AgentState) || "idle",
          },
        });
        break;
      case "run":
        chatFunctions.addAssistantObservation({
          ...baseObservation,
          observation: "run" as const,
          extras: {
            command: String(message.extras.command || ""),
            metadata: message.extras.metadata,
            hidden: Boolean(message.extras.hidden),
          },
        });
        break;
      case "read":
        chatFunctions.addAssistantObservation({
          ...baseObservation,
          observation,
          extras: {
            path: String(message.extras.path || ""),
            impl_source: String(message.extras.impl_source || ""),
          },
        });
        break;
      case "edit":
        chatFunctions.addAssistantObservation({
          ...baseObservation,
          observation,
          extras: {
            path: String(message.extras.path || ""),
            diff: String(message.extras.diff || ""),
            impl_source: String(message.extras.impl_source || ""),
          },
        });
        break;
      case "run_ipython":
        chatFunctions.addAssistantObservation({
          ...baseObservation,
          observation: "run_ipython" as const,
          extras: {
            code: String(message.extras.code || ""),
          },
        });
        break;
      case "delegate":
        chatFunctions.addAssistantObservation({
          ...baseObservation,
          observation: "delegate" as const,
          extras: {
            outputs:
              typeof message.extras.outputs === "object"
                ? (message.extras.outputs as Record<string, unknown>)
                : {},
          },
        });
        break;
      case "browse":
        chatFunctions.addAssistantObservation({
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
            last_browser_action_error: message.extras.last_browser_action_error,
            focused_element_bid: String(
              message.extras.focused_element_bid || "",
            ),
          },
        });
        break;
      case "error":
        chatFunctions.addAssistantObservation({
          ...baseObservation,
          observation: "error" as const,
          source: "user" as const,
          extras: {
            error_id: message.extras.error_id,
          },
        });
        break;
      default:
        // For any unhandled observation types, just ignore them
        break;
    }
  }
}
