import type { Message } from "#/message";
import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsObservation } from "#/types/core/observations";

// This is a singleton service that will be used to update the chat state
// from anywhere in the application
let addUserMessageFn: (payload: {
  content: string;
  imageUrls: string[];
  timestamp: string;
  pending?: boolean;
}) => void = () => {};

let addAssistantMessageFn: (content: string) => void = () => {};

let addAssistantActionFn: (action: OpenHandsAction) => void = () => {};

let addAssistantObservationFn: (
  observation: OpenHandsObservation,
) => void = () => {};

let addErrorMessageFn: (payload: {
  id?: string;
  message: string;
}) => void = () => {};

let clearMessagesFn: () => void = () => {};

let getMessagesFn: () => Message[] = () => [];

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
  addUserMessage: (payload: {
    content: string;
    imageUrls: string[];
    timestamp: string;
    pending?: boolean;
  }) => void;
  addAssistantMessage: (content: string) => void;
  addAssistantAction: (action: OpenHandsAction) => void;
  addAssistantObservation: (observation: OpenHandsObservation) => void;
  addErrorMessage: (payload: { id?: string; message: string }) => void;
  clearMessages: () => void;
  getMessages: () => Message[];
}) {
  addUserMessageFn = addUserMessage;
  addAssistantMessageFn = addAssistantMessage;
  addAssistantActionFn = addAssistantAction;
  addAssistantObservationFn = addAssistantObservation;
  addErrorMessageFn = addErrorMessage;
  clearMessagesFn = clearMessages;
  getMessagesFn = getMessages;
}

// Export the functions to be used anywhere in the application
export function addUserMessage(payload: {
  content: string;
  imageUrls: string[];
  timestamp: string;
  pending?: boolean;
}) {
  addUserMessageFn(payload);
}

export function addAssistantMessage(content: string) {
  addAssistantMessageFn(content);
}

export function addAssistantAction(action: OpenHandsAction) {
  addAssistantActionFn(action);
}

export function addAssistantObservation(observation: OpenHandsObservation) {
  addAssistantObservationFn(observation);
}

export function addErrorMessage(payload: { id?: string; message: string }) {
  addErrorMessageFn(payload);
}

export function clearMessages() {
  clearMessagesFn();
}

export function getMessages() {
  return getMessagesFn();
}
