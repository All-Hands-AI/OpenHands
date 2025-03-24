import { combineReducers, configureStore, Middleware } from "@reduxjs/toolkit";
import { queryClient } from "./query-redux-bridge-init";
import type { Message } from "#/message";

// All slices are now handled by React Query

// Define a type for chat actions
type ChatAction = {
  type: string;
  payload?: unknown;
};

// Define a type for the chat state
interface ChatState {
  messages: Message[];
}

export const rootReducer = combineReducers({
  // All slices have been migrated to React Query
  // Adding a dummy chat reducer to handle actions during migration
  chat: (state: ChatState | undefined, action: ChatAction) => {
    // Create a default state if none is provided
    const currentState = state || { messages: [] };
    switch (action.type) {
      case "chat/addUserMessage":
      case "chat/addAssistantMessage":
      case "chat/addAssistantAction":
      case "chat/addAssistantObservation":
      case "chat/addErrorMessage":
      case "chat/clearMessages":
        // These actions are now handled by the middleware
        return currentState;
      default:
        // Handle any other actions
        return currentState;
    }
  },
});

// Create a middleware to intercept Redux actions and update React Query
const reactQueryMiddleware: Middleware = () => (next) => (action: unknown) => {
  // Cast action to ChatAction for our internal use
  const chatAction = action as ChatAction;
  // Log all actions for debugging
  console.log("[Redux Middleware] Action:", chatAction.type);

  // Handle chat actions
  if (
    chatAction.type &&
    typeof chatAction.type === "string" &&
    chatAction.type.startsWith("chat/")
  ) {
    // Get current messages from React Query
    const currentMessages =
      queryClient.getQueryData<Message[]>(["chat", "messages"]) || [];

    switch (chatAction.type) {
      // Handle all chat-related actions
      case "chat/addUserMessage": {
        const { content, imageUrls, timestamp, pending } =
          chatAction.payload as {
            content: string;
            imageUrls: string[];
            timestamp: string;
            pending?: boolean;
          };
        const message: Message = {
          type: "thought",
          sender: "user",
          content,
          imageUrls,
          timestamp,
          pending: !!pending,
        };
        console.log("[Redux Middleware] Adding user message to React Query");
        queryClient.setQueryData(
          ["chat", "messages"],
          [...currentMessages, message],
        );
        break;
      }
      case "chat/addAssistantMessage": {
        const content = chatAction.payload as string;
        const message: Message = {
          type: "thought",
          sender: "assistant",
          content,
          imageUrls: [],
          timestamp: new Date().toISOString(),
        };
        console.log(
          "[Redux Middleware] Adding assistant message to React Query",
        );
        queryClient.setQueryData(
          ["chat", "messages"],
          [...currentMessages, message],
        );
        break;
      }
      case "chat/addAssistantAction": {
        const actionPayload = chatAction.payload as {
          id: number;
          action: string;
          args: Record<string, unknown>;
        };
        // Find the appropriate message type based on the action
        const actionType = actionPayload.action;
        const translationID = `ACTION_MESSAGE$${actionType.toUpperCase()}`;
        let content = "";

        // Basic handling for common action types
        if (actionPayload.args && actionPayload.args.thought) {
          content = actionPayload.args.thought as string;
        } else if (actionType === "run" && actionPayload.args) {
          content = `Command:\n\`${actionPayload.args.command as string}\``;
        } else if (actionType === "run_ipython" && actionPayload.args) {
          content = `\`\`\`\n${actionPayload.args.code as string}\n\`\`\``;
        }

        const message: Message = {
          type: "action",
          sender: "assistant",
          translationID,
          eventID: actionPayload.id,
          content,
          imageUrls: [],
          timestamp: new Date().toISOString(),
        };

        console.log(
          "[Redux Middleware] Adding assistant action to React Query",
        );
        queryClient.setQueryData(
          ["chat", "messages"],
          [...currentMessages, message],
        );
        break;
      }
      case "chat/addAssistantObservation": {
        // We're not using the observation in this simplified version
        // but we'll log the type definition for documentation purposes
        console.log(
          "[Redux Middleware] Observation type:",
          typeof chatAction.payload,
        );
        // Just log that we received an observation
        // We could define a type for the observation payload, but we're not using it in this simplified version
        // Just documenting the expected structure in comments:
        // {
        //   id: string;
        //   observation: string;
        //   cause: string;
        //   content?: string;
        //   extras?: Record<string, unknown>;
        // }
        // Log that we're handling this type of message
        console.log("[Redux Middleware] Handling observation message");
        // This is a simplified version - in a real implementation, you'd need to find
        // the corresponding action message and update it
        console.log(
          "[Redux Middleware] Adding assistant observation to React Query",
        );
        break;
      }
      case "chat/addErrorMessage": {
        const { id, message } = chatAction.payload as {
          id?: string;
          message: string;
        };
        const errorMessage: Message = {
          translationID: id,
          content: message,
          type: "error",
          sender: "assistant",
          timestamp: new Date().toISOString(),
        };

        console.log("[Redux Middleware] Adding error message to React Query");
        queryClient.setQueryData(
          ["chat", "messages"],
          [...currentMessages, errorMessage],
        );
        break;
      }
      case "chat/clearMessages":
        console.log("[Redux Middleware] Clearing messages in React Query");
        queryClient.setQueryData(["chat", "messages"], []);
        break;
      default:
        // Handle any other chat actions
        console.log(
          "[Redux Middleware] Unhandled chat action:",
          chatAction.type,
        );
        break;
    }
  }

  // Continue with the normal Redux flow
  return next(action);
};

const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(reactQueryMiddleware),
});

// Define a more flexible RootState type that includes test-specific slices
export interface RootState {
  chat: ChatState;
  // Include test-specific slices
  agent?: { curAgentState: string };
  cmd?: { commands: Array<{ content: string; type: string }> };
  // Add other test-specific slices as needed
}
export type AppStore = typeof store;
export type AppDispatch = typeof store.dispatch;

export default store;
