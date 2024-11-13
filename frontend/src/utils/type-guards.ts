import {
  AssistantMessageAction,
  UserMessageAction,
} from "#/types/core/actions";
import { LocalUserMessageAction } from "#/types/core/variances";

const isValidObject = (data: unknown): data is object =>
  typeof data === "object" && data !== null;

export const isLocalUserMessage = (
  message: unknown,
): message is LocalUserMessageAction =>
  isValidObject(message) &&
  "action" in message &&
  message.action === "message" &&
  "args" in message &&
  typeof message.args === "object" &&
  message.args !== null &&
  "content" in message.args &&
  "image_urls" in message.args;

export const isUserMessageAction = (
  message: unknown,
): message is UserMessageAction =>
  isValidObject(message) &&
  "action" in message &&
  message.action === "message" &&
  "source" in message &&
  message.source === "user";

export const isAssistantMessageAction = (
  message: unknown,
): message is AssistantMessageAction =>
  isValidObject(message) &&
  "action" in message &&
  message.action === "message" &&
  "source" in message &&
  message.source === "agent";
