import { OpenHandsParsedEvent } from ".";
import {
  UserMessageAction,
  AssistantMessageAction,
  OpenHandsAction,
  SystemMessageAction,
} from "./actions";
import {
  CommandObservation,
  ErrorObservation,
  OpenHandsObservation,
} from "./observations";

export const isOpenHandsAction = (
  event: OpenHandsParsedEvent,
): event is OpenHandsAction => "action" in event;

export const isOpenHandsObservation = (
  event: OpenHandsParsedEvent,
): event is OpenHandsObservation => "observation" in event;

export const isUserMessage = (
  event: OpenHandsParsedEvent,
): event is UserMessageAction =>
  isOpenHandsAction(event) &&
  event.source === "user" &&
  event.action === "message";

export const isAssistantMessage = (
  event: OpenHandsParsedEvent,
): event is AssistantMessageAction =>
  isOpenHandsAction(event) &&
  event.source === "agent" &&
  (event.action === "message" || event.action === "finish");

export const isErrorObservation = (
  event: OpenHandsParsedEvent,
): event is ErrorObservation =>
  isOpenHandsObservation(event) && event.observation === "error";

export const isCommandObservation = (
  event: OpenHandsParsedEvent,
): event is CommandObservation =>
  isOpenHandsObservation(event) && event.observation === "run";

export const isFinishAction = (
  event: OpenHandsParsedEvent,
): event is AssistantMessageAction =>
  isOpenHandsAction(event) && event.action === "finish";

export const isSystemMessage = (
  event: OpenHandsParsedEvent,
): event is SystemMessageAction =>
  isOpenHandsAction(event) && event.action === "system";

export const isRejectObservation = (
  event: OpenHandsParsedEvent,
): event is OpenHandsObservation =>
  isOpenHandsObservation(event) && event.observation === "user_rejected";
