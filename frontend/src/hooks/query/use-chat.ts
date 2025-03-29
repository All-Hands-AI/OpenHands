import { useQueryClient, useQuery } from "@tanstack/react-query";
import { Message } from "#/message";
import { ActionSecurityRisk } from "#/hooks/query/use-security-analyzer";
import {
  OpenHandsObservation,
  CommandObservation,
  IPythonObservation,
} from "#/types/core/observations";
import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsEventType } from "#/types/core/base";

const MAX_CONTENT_LENGTH = 1000;

const HANDLED_ACTIONS: OpenHandsEventType[] = [
  "run",
  "run_ipython",
  "write",
  "read",
  "browse",
];

export const CHAT_QUERY_KEY = ["chat"];

function getRiskText(risk: ActionSecurityRisk) {
  switch (risk) {
    case ActionSecurityRisk.LOW:
      return "Low Risk";
    case ActionSecurityRisk.MEDIUM:
      return "Medium Risk";
    case ActionSecurityRisk.HIGH:
      return "High Risk";
    case ActionSecurityRisk.UNKNOWN:
    default:
      return "Unknown Risk";
  }
}
export function addUserMessage(
  queryClient: ReturnType<typeof useQueryClient>,
  payload: {
    content: string;
    imageUrls: string[];
    timestamp: string;
    pending?: boolean;
  },
) {
  const message: Message = {
    type: "thought",
    sender: "user",
    content: payload.content,
    imageUrls: payload.imageUrls,
    timestamp: payload.timestamp || new Date().toISOString(),
    pending: !!payload.pending,
  };

  const currentState = queryClient.getQueryData<{ messages: Message[] }>(
    CHAT_QUERY_KEY,
  ) || { messages: [] };

  const updatedMessages = [...currentState.messages];
  let i = updatedMessages.length;
  while (i) {
    i -= 1;
    const m = updatedMessages[i] as Message;
    if (m.pending) {
      updatedMessages.splice(i, 1);
    }
  }

  updatedMessages.push(message);

  queryClient.setQueryData(CHAT_QUERY_KEY, { messages: updatedMessages });
}

export function addAssistantMessage(
  queryClient: ReturnType<typeof useQueryClient>,
  content: string,
) {
  const message: Message = {
    type: "thought",
    sender: "assistant",
    content,
    imageUrls: [],
    timestamp: new Date().toISOString(),
    pending: false,
  };

  const currentState = queryClient.getQueryData<{ messages: Message[] }>(
    CHAT_QUERY_KEY,
  ) || { messages: [] };
  const updatedMessages = [...currentState.messages, message];

  queryClient.setQueryData(CHAT_QUERY_KEY, { messages: updatedMessages });
}

export function addAssistantAction(
  queryClient: ReturnType<typeof useQueryClient>,
  action: OpenHandsAction,
) {
  const actionID = action.action;
  if (!HANDLED_ACTIONS.includes(actionID)) {
    return;
  }

  const translationID = `ACTION_MESSAGE$${actionID.toUpperCase()}`;
  let text = "";
  if (actionID === "run") {
    text = `Command:\n\`${action.args.command}\``;
  } else if (actionID === "run_ipython") {
    text = `\`\`\`\n${action.args.code}\n\`\`\``;
  } else if (actionID === "write") {
    let { content } = action.args;
    if (content.length > MAX_CONTENT_LENGTH) {
      content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
    }
    text = `${action.args.path}\n${content}`;
  } else if (actionID === "browse") {
    text = `Browsing ${action.args.url}`;
  }

  if (actionID === "run" || actionID === "run_ipython") {
    if (action.args.confirmation_state === "awaiting_confirmation") {
      text += `\n\n${getRiskText(
        action.args.security_risk as unknown as ActionSecurityRisk,
      )}`;
    }
  } else if (actionID === "think") {
    text = action.args.thought;
  }

  const message: Message = {
    type: "action",
    sender: "assistant",
    translationID,
    eventID: action.id,
    content: text,
    imageUrls: [],
    timestamp: new Date().toISOString(),
  };

  const currentState = queryClient.getQueryData<{ messages: Message[] }>(
    CHAT_QUERY_KEY,
  ) || { messages: [] };
  const updatedMessages = [...currentState.messages, message];

  queryClient.setQueryData(CHAT_QUERY_KEY, { messages: updatedMessages });
}

export function addAssistantObservation(
  queryClient: ReturnType<typeof useQueryClient>,
  observation: OpenHandsObservation,
) {
  const observationID = observation.observation;
  if (!HANDLED_ACTIONS.includes(observationID)) {
    return;
  }

  const translationID = `OBSERVATION_MESSAGE$${observationID.toUpperCase()}`;
  const causeID = observation.cause;

  const currentState = queryClient.getQueryData<{ messages: Message[] }>(
    CHAT_QUERY_KEY,
  ) || { messages: [] };
  const updatedMessages = [...currentState.messages];

  const causeMessageIndex = updatedMessages.findIndex(
    (message) => message.eventID === causeID,
  );

  if (causeMessageIndex === -1) {
    return;
  }

  const causeMessage = { ...updatedMessages[causeMessageIndex] };
  causeMessage.translationID = translationID;

  if (observationID === "run") {
    const commandObs = observation as CommandObservation;
    causeMessage.success = commandObs.extras.metadata.exit_code === 0;
  } else if (observationID === "run_ipython") {
    const ipythonObs = observation as IPythonObservation;
    causeMessage.success = !ipythonObs.content.toLowerCase().includes("error:");
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

  if (observationID === "run" || observationID === "run_ipython") {
    let { content } = observation;
    if (content.length > MAX_CONTENT_LENGTH) {
      content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
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
    if (content.length > MAX_CONTENT_LENGTH) {
      content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
    }
    causeMessage.content = content;
  }

  updatedMessages[causeMessageIndex] = causeMessage;

  queryClient.setQueryData(CHAT_QUERY_KEY, { messages: updatedMessages });
}

export function addErrorMessage(
  queryClient: ReturnType<typeof useQueryClient>,
  payload: { id?: string; message: string },
) {
  const { id, message } = payload;

  const errorMessage: Message = {
    translationID: id,
    content: message,
    type: "error",
    sender: "assistant",
    timestamp: new Date().toISOString(),
  };

  const currentState = queryClient.getQueryData<{ messages: Message[] }>(
    CHAT_QUERY_KEY,
  ) || { messages: [] };
  const updatedMessages = [...currentState.messages, errorMessage];

  queryClient.setQueryData(CHAT_QUERY_KEY, { messages: updatedMessages });
}

export function clearMessages(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.setQueryData(CHAT_QUERY_KEY, { messages: [] });
}

export function useChat() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: CHAT_QUERY_KEY,
    queryFn: () => ({ messages: [] }),
    initialData: { messages: [] },
  });

  return {
    messages: query.data?.messages || [],
    isLoading: query.isLoading,
    addUserMessage: (payload: {
      content: string;
      imageUrls: string[];
      timestamp: string;
      pending?: boolean;
    }) => addUserMessage(queryClient, payload),
    addAssistantMessage: (content: string) =>
      addAssistantMessage(queryClient, content),
    addAssistantAction: (action: OpenHandsAction) =>
      addAssistantAction(queryClient, action),
    addAssistantObservation: (observation: OpenHandsObservation) =>
      addAssistantObservation(queryClient, observation),
    addErrorMessage: (payload: { id?: string; message: string }) =>
      addErrorMessage(queryClient, payload),
    clearMessages: () => clearMessages(queryClient),
  };
}
