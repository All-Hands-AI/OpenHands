import { setCurrentAgentState } from "#/state/agent-slice";
import store from "#/store";
import { queryClient } from "#/query-redux-bridge-init";
import { ObservationMessage } from "#/types/message";
import { AgentState } from "#/types/agent-state";
// Command slice is now handled by React Query
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

      // Update command state in React Query
      const currentState = queryClient.getQueryData<{
        commands: Array<{ content: string; type: string }>;
      }>(["command"]) || { commands: [] };

      // eslint-disable-next-line no-console
      console.log("[Command Debug] Handling RUN observation:", {
        contentLength: content.length,
        currentCommandsLength: currentState.commands.length,
      });

      queryClient.setQueryData(["command"], {
        ...currentState,
        commands: [...currentState.commands, { content, type: "output" }],
      });
      break;
    }
    case ObservationType.RUN_IPYTHON:
      // FIXME: render this as markdown
      store.dispatch(appendJupyterOutput(message.content));
      break;
    case ObservationType.BROWSE:
      // eslint-disable-next-line no-console
      console.log("[Browser Debug] Received BROWSE observation:", {
        hasScreenshot: !!message.extras?.screenshot,
        url: message.extras?.url,
        screenshotLength: message.extras?.screenshot
          ? message.extras.screenshot.length
          : 0,
      });

      if (message.extras?.screenshot) {
        // Update browser state in React Query
        const currentState = queryClient.getQueryData<{
          url: string;
          screenshotSrc: string;
        }>(["browser"]) || { url: "", screenshotSrc: "" };

        // eslint-disable-next-line no-console
        console.log(
          "[Browser Debug] Current state before screenshot update:",
          currentState,
        );

        const newState = {
          ...currentState,
          screenshotSrc: message.extras.screenshot,
        };

        // eslint-disable-next-line no-console
        console.log("[Browser Debug] New state after screenshot update:", {
          ...newState,
          screenshotSrc: newState.screenshotSrc
            ? `data present (length: ${newState.screenshotSrc.length})`
            : "empty",
        });

        queryClient.setQueryData(["browser"], newState);
      }

      if (message.extras?.url) {
        // Update browser state in React Query
        const currentState = queryClient.getQueryData<{
          url: string;
          screenshotSrc: string;
        }>(["browser"]) || { url: "", screenshotSrc: "" };

        // eslint-disable-next-line no-console
        console.log(
          "[Browser Debug] Current state before URL update:",
          currentState,
        );

        const newState = {
          ...currentState,
          url: message.extras.url,
        };

        // eslint-disable-next-line no-console
        console.log("[Browser Debug] New state after URL update:", newState);

        queryClient.setQueryData(["browser"], newState);
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
    case ObservationType.THINK:
    case ObservationType.NULL:
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
        store.dispatch(
          addAssistantObservation({
            ...baseObservation,
            observation,
            extras: {
              path: String(message.extras.path || ""),
              impl_source: String(message.extras.impl_source || ""),
            },
          }),
        );
        break;
      case "edit":
        store.dispatch(
          addAssistantObservation({
            ...baseObservation,
            observation,
            extras: {
              path: String(message.extras.path || ""),
              diff: String(message.extras.diff || ""),
              impl_source: String(message.extras.impl_source || ""),
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
