import type { Message } from "#/message";
import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsObservation } from "#/types/core/observations";

// Function types
type UserMessageFn = (payload: {
  content: string;
  imageUrls: string[];
  timestamp: string;
  pending?: boolean;
}) => void;

type AssistantMessageFn = (content: string) => void;
type AssistantActionFn = (action: OpenHandsAction) => void;
type AssistantObservationFn = (observation: OpenHandsObservation) => void;
type ErrorMessageFn = (payload: { id?: string; message: string }) => void;
type ClearMessagesFn = () => void;
type GetMessagesFn = () => Message[];

// Module-level variables to store the actual functions
let userMessageImpl: UserMessageFn = () => {};
let assistantMessageImpl: AssistantMessageFn = () => {};
let assistantActionImpl: AssistantActionFn = () => {};
let assistantObservationImpl: AssistantObservationFn = () => {};
let errorMessageImpl: ErrorMessageFn = () => {};
let clearMessagesImpl: ClearMessagesFn = () => {};
let getMessagesImpl: GetMessagesFn = () => [];

// Register the functions from the context
export function registerChatFunctions({
  addUserMessage,
  addAssistantMessage,
  addAssistantAction,
  addAssistantObservation,
  addErrorMessage,
  clearMessages,
  getMessages,
}: {
  addUserMessage: UserMessageFn;
  addAssistantMessage: AssistantMessageFn;
  addAssistantAction: AssistantActionFn;
  addAssistantObservation: AssistantObservationFn;
  addErrorMessage: ErrorMessageFn;
  clearMessages: ClearMessagesFn;
  getMessages: GetMessagesFn;
}): void {
  userMessageImpl = addUserMessage;
  assistantMessageImpl = addAssistantMessage;
  assistantActionImpl = addAssistantAction;
  assistantObservationImpl = addAssistantObservation;
  errorMessageImpl = addErrorMessage;
  clearMessagesImpl = clearMessages;
  getMessagesImpl = getMessages;
}

// Export the service functions
export const ChatService = {
  addUserMessage: (payload: {
    content: string;
    imageUrls: string[];
    timestamp: string;
    pending?: boolean;
  }): void => {
    userMessageImpl(payload);
  },

  addAssistantMessage: (content: string): void => {
    assistantMessageImpl(content);
  },

  addAssistantAction: (action: OpenHandsAction): void => {
    assistantActionImpl(action);
  },

  addAssistantObservation: (observation: OpenHandsObservation): void => {
    assistantObservationImpl(observation);
  },

  addErrorMessage: (payload: { id?: string; message: string }): void => {
    errorMessageImpl(payload);
  },

  clearMessages: (): void => {
    clearMessagesImpl();
  },

  getMessages: (): Message[] => getMessagesImpl(),
};

// Re-export the service functions for convenience
export const {
  addUserMessage,
  addAssistantMessage,
  addAssistantAction,
  addAssistantObservation,
  addErrorMessage,
  clearMessages,
  getMessages,
} = ChatService;
