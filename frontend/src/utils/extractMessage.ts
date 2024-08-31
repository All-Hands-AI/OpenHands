import { OpenHandsParsedEvent } from "#/types/core";
import {
  UserMessageAction,
  AssistantMessageAction,
  IPythonAction,
  FinishAction,
  CommandAction,
  DelegateAction,
  BrowseAction,
  BrowseInteractiveAction,
  RejectAction,
} from "#/types/core/actions";
import { DelegateObservation } from "#/types/core/observations";

const isMessage = (
  message: OpenHandsParsedEvent,
): message is UserMessageAction | AssistantMessageAction =>
  "action" in message && message.action === "message";

const isIPythonAction = (
  message: OpenHandsParsedEvent,
): message is IPythonAction =>
  "action" in message && message.action === "run_ipython";

const isCommandAction = (
  message: OpenHandsParsedEvent,
): message is CommandAction => "action" in message && message.action === "run";

const isFinishAction = (
  message: OpenHandsParsedEvent,
): message is FinishAction =>
  "action" in message && message.action === "finish";

const isDelegateAction = (
  message: OpenHandsParsedEvent,
): message is DelegateAction =>
  "action" in message && message.action === "delegate";

const isBrowseAction = (
  message: OpenHandsParsedEvent,
): message is BrowseAction =>
  "action" in message && message.action === "browse";

const isBrowseInteractiveAction = (
  message: OpenHandsParsedEvent,
): message is BrowseInteractiveAction =>
  "action" in message && message.action === "browse_interactive";

const isRejectAction = (
  message: OpenHandsParsedEvent,
): message is RejectAction =>
  "action" in message && message.action === "reject";

const isDelegateObservation = (
  message: OpenHandsParsedEvent,
): message is DelegateObservation =>
  "observation" in message && message.observation === "delegate";

export interface ParsedMessage {
  source: "assistant" | "user";
  content: string;
  imageUrls: string[];
}

export const extractMessage = (
  message: OpenHandsParsedEvent,
): ParsedMessage | null => {
  if (isMessage(message)) {
    return {
      source: message.source === "agent" ? "assistant" : "user",
      content: message.args.content,
      imageUrls: message.args.images_urls ?? [],
    };
  }

  if (
    isIPythonAction(message) ||
    isCommandAction(message) ||
    isBrowseInteractiveAction(message)
  ) {
    return {
      source: "assistant",
      content: message.args.thought || message.message,
      imageUrls: [],
    };
  }

  if (
    isFinishAction(message) ||
    isDelegateAction(message) ||
    isBrowseAction(message) ||
    isRejectAction(message)
  ) {
    return {
      source: "assistant",
      content: message.message,
      imageUrls: [],
    };
  }

  if (isDelegateObservation(message)) {
    return {
      source: "assistant",
      content: message.content,
      imageUrls: [],
    };
  }

  return null;
};
