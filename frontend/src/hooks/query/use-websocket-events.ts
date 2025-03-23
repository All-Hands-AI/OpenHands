import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useWsClient } from "#/context/ws-client-provider";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";
import {
  ActionMessage,
  ObservationMessage,
  StatusMessage,
} from "#/types/message";
import ActionType from "#/types/action-type";
import ObservationType from "#/types/observation-type";

// Forward declarations to avoid use-before-define errors
let handleActionMessage: (
  message: ActionMessage,
  queryClient: ReturnType<typeof useQueryClient>,
  bridge: ReturnType<typeof getQueryReduxBridge>,
) => void;

let handleObservationMessage: (
  message: ObservationMessage,
  queryClient: ReturnType<typeof useQueryClient>,
  bridge: ReturnType<typeof getQueryReduxBridge>,
) => void;

let handleStatusMessage: (
  message: StatusMessage,
  queryClient: ReturnType<typeof useQueryClient>,
  bridge: ReturnType<typeof getQueryReduxBridge>,
) => void;

/**
 * Hook to handle websocket events for React Query
 * This provides a parallel implementation to the Redux event handlers
 * but updates React Query cache instead of dispatching Redux actions
 */
export function useWebsocketEvents() {
  const queryClient = useQueryClient();
  const { events } = useWsClient();
  const bridge = getQueryReduxBridge();

  useEffect(() => {
    if (!events.length) return;

    // Process only the latest event
    const latestEvent = events[events.length - 1];

    if (!latestEvent) return;

    // Handle different event types
    if ("action" in latestEvent) {
      handleActionMessage(
        latestEvent as unknown as ActionMessage,
        queryClient,
        bridge,
      );
    } else if ("observation" in latestEvent) {
      handleObservationMessage(
        latestEvent as unknown as ObservationMessage,
        queryClient,
        bridge,
      );
    } else if ("status_update" in latestEvent) {
      handleStatusMessage(
        latestEvent as unknown as StatusMessage,
        queryClient,
        bridge,
      );
    }
  }, [events, queryClient]);

  return null;
}

// Handle action messages (parallel to handleActionMessage in services/actions.ts)
handleActionMessage = (
  message: ActionMessage,
  queryClient: ReturnType<typeof useQueryClient>,
  bridge: ReturnType<typeof getQueryReduxBridge>,
) => {
  if (message.args?.hidden) {
    return;
  }

  // Update metrics if available and if metrics slice is migrated
  if (
    bridge.isSliceMigrated("metrics") &&
    (message.llm_metrics || message.tool_call_metadata?.model_response?.usage)
  ) {
    const metrics = {
      cost: message.llm_metrics?.accumulated_cost ?? null,
      usage: message.tool_call_metadata?.model_response?.usage ?? null,
    };
    queryClient.setQueryData(["metrics"], metrics);
  }

  // Handle command input if command slice is migrated
  if (bridge.isSliceMigrated("command") && message.action === ActionType.RUN) {
    const currentCommands =
      queryClient.getQueryData<string[]>(["command", "inputs"]) || [];
    queryClient.setQueryData(
      ["command", "inputs"],
      [...currentCommands, message.args.command],
    );
  }

  // Handle security analyzer input if securityAnalyzer slice is migrated
  if (
    bridge.isSliceMigrated("securityAnalyzer") &&
    "args" in message &&
    "security_risk" in message.args
  ) {
    const currentInputs =
      queryClient.getQueryData<ActionMessage[]>([
        "securityAnalyzer",
        "inputs",
      ]) || [];
    queryClient.setQueryData(
      ["securityAnalyzer", "inputs"],
      [...currentInputs, message],
    );
  }

  // Handle agent messages if chat slice is migrated
  if (bridge.isSliceMigrated("chat") && message.source === "agent") {
    // Handle thought messages
    if (message.args && message.args.thought) {
      const messages =
        queryClient.getQueryData<Record<string, unknown>[]>([
          "chat",
          "messages",
        ]) || [];
      queryClient.setQueryData(
        ["chat", "messages"],
        [
          ...messages,
          {
            type: "thought",
            sender: "assistant",
            content: message.args.thought,
            imageUrls: [],
            timestamp: new Date().toISOString(),
            pending: false,
          },
        ],
      );
    }

    // Handle action messages
    const HANDLED_ACTIONS: string[] = [
      "run",
      "run_ipython",
      "write",
      "read",
      "browse",
      "edit",
    ];

    const actionID = message.action;
    if (HANDLED_ACTIONS.includes(actionID)) {
      const translationID = `ACTION_MESSAGE$${actionID.toUpperCase()}`;
      let text = "";

      if (actionID === "run") {
        text = `Command:\n\`${message.args.command}\``;
      } else if (actionID === "run_ipython") {
        text = `\`\`\`\n${message.args.code}\n\`\`\``;
      } else if (actionID === "write") {
        let { content } = message.args;
        const MAX_CONTENT_LENGTH = 1000;
        if (content.length > MAX_CONTENT_LENGTH) {
          content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
        }
        text = `${message.args.path}\n${content}`;
      } else if (actionID === "browse") {
        text = `Browsing ${message.args.url}`;
      } else if (actionID === "think") {
        text = message.args.thought;
      } else {
        // Default case
        text = `Action: ${actionID}`;
      }

      if (actionID === "run" || actionID === "run_ipython") {
        if (message.args.confirmation_state === "awaiting_confirmation") {
          let riskText = "Unknown Risk";
          switch (message.args.security_risk) {
            case "LOW":
              riskText = "Low Risk";
              break;
            case "MEDIUM":
              riskText = "Medium Risk";
              break;
            case "HIGH":
              riskText = "High Risk";
              break;
            default:
              riskText = "Unknown Risk";
              break;
          }
          text += `\n\n${riskText}`;
        }
      }

      const messages =
        queryClient.getQueryData<Record<string, unknown>[]>([
          "chat",
          "messages",
        ]) || [];
      queryClient.setQueryData(
        ["chat", "messages"],
        [
          ...messages,
          {
            type: "action",
            sender: "assistant",
            translationID,
            eventID: message.id,
            content: text,
            imageUrls: [],
            timestamp: new Date().toISOString(),
          },
        ],
      );
    }
  }

  // Handle specific action types
  switch (message.action) {
    case ActionType.BROWSE:
    case ActionType.BROWSE_INTERACTIVE:
      if (
        bridge.isSliceMigrated("chat") &&
        !message.args.thought &&
        message.message
      ) {
        const messages =
          queryClient.getQueryData<Record<string, unknown>[]>([
            "chat",
            "messages",
          ]) || [];
        queryClient.setQueryData(
          ["chat", "messages"],
          [
            ...messages,
            {
              type: "thought",
              sender: "assistant",
              content: message.message,
              imageUrls: [],
              timestamp: new Date().toISOString(),
              pending: false,
            },
          ],
        );
      }
      break;

    case ActionType.WRITE:
      if (bridge.isSliceMigrated("code")) {
        const { path, content } = message.args;
        queryClient.setQueryData(["code", "activeFilepath"], path);
        queryClient.setQueryData(["code", "content"], content);
      }
      break;

    case ActionType.MESSAGE:
      if (bridge.isSliceMigrated("chat")) {
        if (message.source === "user") {
          const messages =
            queryClient.getQueryData<Record<string, unknown>[]>([
              "chat",
              "messages",
            ]) || [];
          queryClient.setQueryData(
            ["chat", "messages"],
            [
              ...messages,
              {
                type: "thought",
                sender: "user",
                content: message.args.content,
                imageUrls:
                  typeof message.args.image_urls === "string"
                    ? [message.args.image_urls]
                    : message.args.image_urls,
                timestamp: message.timestamp || new Date().toISOString(),
                pending: false,
              },
            ],
          );
        } else {
          const messages =
            queryClient.getQueryData<Record<string, unknown>[]>([
              "chat",
              "messages",
            ]) || [];
          queryClient.setQueryData(
            ["chat", "messages"],
            [
              ...messages,
              {
                type: "thought",
                sender: "assistant",
                content: message.args.content,
                imageUrls: [],
                timestamp: new Date().toISOString(),
                pending: false,
              },
            ],
          );
        }
      }
      break;

    case ActionType.RUN_IPYTHON:
      if (
        bridge.isSliceMigrated("jupyter") &&
        message.args.confirmation_state !== "rejected"
      ) {
        const inputs =
          queryClient.getQueryData<string[]>(["jupyter", "inputs"]) || [];
        queryClient.setQueryData(
          ["jupyter", "inputs"],
          [...inputs, message.args.code],
        );
      }
      break;

    case ActionType.FINISH:
      if (bridge.isSliceMigrated("chat")) {
        const messages =
          queryClient.getQueryData<Record<string, unknown>[]>([
            "chat",
            "messages",
          ]) || [];

        // Add final thought
        queryClient.setQueryData(
          ["chat", "messages"],
          [
            ...messages,
            {
              type: "thought",
              sender: "assistant",
              content: message.args.final_thought,
              imageUrls: [],
              timestamp: new Date().toISOString(),
              pending: false,
            },
          ],
        );

        // Add success prediction if available
        let successPrediction = "";
        if (message.args.task_completed === "partial") {
          successPrediction =
            "I believe that the task was **completed partially**.";
        } else if (message.args.task_completed === "false") {
          successPrediction = "I believe that the task was **not completed**.";
        } else if (message.args.task_completed === "true") {
          successPrediction =
            "I believe that the task was **completed successfully**.";
        }

        if (successPrediction) {
          const updatedMessages =
            queryClient.getQueryData<Record<string, unknown>[]>([
              "chat",
              "messages",
            ]) || [];
          queryClient.setQueryData(
            ["chat", "messages"],
            [
              ...updatedMessages,
              {
                type: "thought",
                sender: "assistant",
                content: message.args.final_thought
                  ? `\n${successPrediction}`
                  : successPrediction,
                imageUrls: [],
                timestamp: new Date().toISOString(),
                pending: false,
              },
            ],
          );
        }
      }
      break;
    default:
      // Handle any other action types
      break;
  }
};

// Handle observation messages (parallel to handleObservationMessage in services/observations.ts)
handleObservationMessage = (
  message: ObservationMessage,
  queryClient: ReturnType<typeof useQueryClient>,
  bridge: ReturnType<typeof getQueryReduxBridge>,
) => {
  switch (message.observation) {
    case ObservationType.RUN:
      if (message.extras.hidden) break;

      if (bridge.isSliceMigrated("command")) {
        let { content } = message;
        if (content.length > 5000) {
          const head = content.slice(0, 5000);
          content = `${head}\r\n\n... (truncated ${message.content.length - 5000} characters) ...`;
        }

        const outputs =
          queryClient.getQueryData<string[]>(["command", "outputs"]) || [];
        queryClient.setQueryData(["command", "outputs"], [...outputs, content]);
      }
      break;

    case ObservationType.RUN_IPYTHON:
      if (bridge.isSliceMigrated("jupyter")) {
        const outputs =
          queryClient.getQueryData<string[]>(["jupyter", "outputs"]) || [];
        queryClient.setQueryData(
          ["jupyter", "outputs"],
          [...outputs, message.content],
        );
      }
      break;

    case ObservationType.BROWSE:
      if (bridge.isSliceMigrated("browser")) {
        if (message.extras?.screenshot) {
          queryClient.setQueryData(
            ["browser", "screenshotSrc"],
            message.extras.screenshot,
          );
        }
        if (message.extras?.url) {
          queryClient.setQueryData(["browser", "url"], message.extras.url);
        }
      }
      break;

    case ObservationType.AGENT_STATE_CHANGED:
      if (bridge.isSliceMigrated("agent")) {
        queryClient.setQueryData(
          ["agent", "currentState"],
          message.extras.agent_state,
        );
      }
      break;

    case ObservationType.DELEGATE:
      if (bridge.isSliceMigrated("chat") && message.content) {
        const messages =
          queryClient.getQueryData<Record<string, unknown>[]>([
            "chat",
            "messages",
          ]) || [];
        queryClient.setQueryData(
          ["chat", "messages"],
          [
            ...messages,
            {
              type: "thought",
              sender: "assistant",
              content: message.content,
              imageUrls: [],
              timestamp: new Date().toISOString(),
              pending: false,
            },
          ],
        );
      }
      break;
    default:
      // Default case for other observation types
      break;
  }

  // Update chat messages with observation data
  if (bridge.isSliceMigrated("chat") && !message.extras?.hidden) {
    const { observation } = message;
    const messages =
      queryClient.getQueryData<Record<string, unknown>[]>([
        "chat",
        "messages",
      ]) || [];

    // Find the message that caused this observation
    const causeID = message.cause;
    const causeMessageIndex = messages.findIndex(
      (msg) => msg.eventID === causeID,
    );

    if (causeMessageIndex !== -1) {
      const causeMessage = { ...messages[causeMessageIndex] };
      const translationID = `OBSERVATION_MESSAGE$${observation.toUpperCase()}`;
      causeMessage.translationID = translationID;

      // Set success property based on observation type
      if (observation === "run") {
        causeMessage.success = message.extras.metadata.exit_code === 0;
      } else if (observation === "run_ipython") {
        causeMessage.success = !message.content
          .toLowerCase()
          .includes("error:");
      } else if (observation === "read" || observation === "edit") {
        if (message.extras.impl_source === "oh_aci") {
          causeMessage.success =
            message.content.length > 0 &&
            !message.content.startsWith("ERROR:\n");
        } else {
          causeMessage.success =
            message.content.length > 0 &&
            !message.content.toLowerCase().includes("error:");
        }
      }

      // Update content based on observation type
      if (observation === "run" || observation === "run_ipython") {
        let { content } = message;
        const MAX_CONTENT_LENGTH = 1000;
        if (content.length > MAX_CONTENT_LENGTH) {
          content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
        }
        causeMessage.content = `${
          causeMessage.content
        }\n\nOutput:\n\`\`\`\n${content.trim() || "[Command finished execution with no output]"}\n\`\`\``;
      } else if (observation === "read") {
        causeMessage.content = `\`\`\`\n${message.content}\n\`\`\``;
      } else if (observation === "edit") {
        if (causeMessage.success) {
          causeMessage.content = `\`\`\`diff\n${message.extras.diff}\n\`\`\``;
        } else {
          causeMessage.content = message.content;
        }
      } else if (observation === "browse") {
        let content = `**URL:** ${message.extras.url}\n`;
        if (message.extras.error) {
          content += `**Error:**\n${message.extras.error}\n`;
        }
        content += `**Output:**\n${message.content}`;
        const MAX_CONTENT_LENGTH = 1000;
        if (content.length > MAX_CONTENT_LENGTH) {
          content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
        }
        causeMessage.content = content;
      }

      // Update the message in the array
      const updatedMessages = [...messages];
      updatedMessages[causeMessageIndex] = causeMessage;
      queryClient.setQueryData(["chat", "messages"], updatedMessages);
    }
  }
};

// Handle status messages (parallel to handleStatusMessage in services/actions.ts)
handleStatusMessage = (
  message: StatusMessage,
  queryClient: ReturnType<typeof useQueryClient>,
  bridge: ReturnType<typeof getQueryReduxBridge>,
) => {
  if (message.type === "info" && bridge.isSliceMigrated("status")) {
    queryClient.setQueryData(["status", "currentMessage"], message);
  } else if (message.type === "error" && bridge.isSliceMigrated("chat")) {
    const messages =
      queryClient.getQueryData<Record<string, unknown>[]>([
        "chat",
        "messages",
      ]) || [];
    queryClient.setQueryData(
      ["chat", "messages"],
      [
        ...messages,
        {
          translationID: message.id,
          content: message.message,
          type: "error",
          sender: "assistant",
          timestamp: new Date().toISOString(),
        },
      ],
    );
  } else {
    // Default case
    console.warn("Unhandled status message type:", message.type);
  }
};
