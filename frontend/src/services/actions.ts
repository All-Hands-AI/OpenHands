import { ActionMessage } from "#/types/message";
import ActionType from "#/types/action-type";
import { updateAgentState } from "#/services/context-services/agent-state-service";
import { updateStatus } from "#/services/context-services/status-service";
import {
  addUserMessage,
  addAssistantMessage,
  addAssistantAction,
  addErrorMessage,
} from "#/services/context-services/chat-service";

export function handleActionMessage(message: ActionMessage) {
  // Handle different action types
  switch (message.type) {
    case ActionType.AGENT_STATE_CHANGED: {
      updateAgentState(message.args.agent_state);
      break;
    }
    case ActionType.TASK_COMPLETION: {
      // Add a message to the chat with the task completion status
      let successPrediction = "";
      if (message.args.task_completed === "true") {
        successPrediction =
          "I believe that the task was **completed successfully**.";
      } else if (message.args.task_completed === "false") {
        successPrediction =
          "I believe that the task was **not completed successfully**.";
      } else if (message.args.task_completed === "partial") {
        successPrediction =
          "I believe that the task was **completed partially**.";
      }
      if (successPrediction) {
        // if final_thought is not empty, add a new line before the success prediction
        if (message.args.final_thought) {
          addAssistantMessage(`\n${successPrediction}`);
        } else {
          addAssistantMessage(successPrediction);
        }
      }
      break;
    }
    case ActionType.MESSAGE: {
      if (message.source === "user") {
        addUserMessage({
          content: message.args.content,
          imageUrls:
            typeof message.args.image_urls === "string"
              ? [message.args.image_urls]
              : message.args.image_urls,
          timestamp: message.timestamp,
          pending: false,
        });
      } else if (message.source === "assistant") {
        addAssistantMessage(message.args.content);
      }
      break;
    }
    case ActionType.ASSISTANT_ACTION: {
      addAssistantAction({
        id: message.id,
        timestamp: message.timestamp,
        action: message.args.action,
        args: message.args.args,
      });
      break;
    }
    default: {
      // Log unknown action type
      break;
    }
  }
}

export function handleStatusMessage(message: {
  id: string;
  message: string;
  type: "info" | "error" | "warning" | "success";
  status_update?: boolean;
}) {
  // Update the status
  updateStatus({
    id: message.id,
    message: message.message,
    type: message.type,
  });

  // If it's an error, also add it to the chat
  if (message.type === "error") {
    // Only add to chat if it's not a status update
    if (!message.status_update) {
      addErrorMessage({
        message: message.message,
      });
    }
  }
}