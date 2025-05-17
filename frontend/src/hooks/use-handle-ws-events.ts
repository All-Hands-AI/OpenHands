import React from "react";
import { useDispatch } from "react-redux";
import { useTranslation } from "react-i18next";
import { useWsClient } from "#/context/ws-client-provider";
import { generateAgentStateChangeEvent } from "#/services/agent-state-service";
import { addErrorMessage } from "#/state/chat-slice";
import { AgentState } from "#/types/agent-state";
import { ErrorObservation } from "#/types/core/observations";
import { useEndSession } from "./use-end-session";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { setAgentType, setDelegationState } from "#/state/agent-slice";
import ActionType from "#/types/action-type";
import { I18nKey } from "#/i18n/declaration";

interface ServerError {
  error: boolean | string;
  message: string;
  [key: string]: unknown;
}

const isServerError = (data: object): data is ServerError => "error" in data;

const isErrorObservation = (data: object): data is ErrorObservation =>
  "observation" in data && data.observation === "error";

export const useHandleWSEvents = () => {
  const { events, send } = useWsClient();
  const dispatch = useDispatch();
  const { t } = useTranslation();

  React.useEffect(() => {
    if (!events.length) {
      return;
    }
    const event = events[events.length - 1];

    if (isServerError(event)) {
      if (event.error_code === 401) {
        displayErrorToast("Session expired.");
        return;
      }

      if (typeof event.error === "string") {
        displayErrorToast(event.error);
      } else {
        displayErrorToast(event.message);
      }
      return;
    }

    if (event.type === "error") {
      const message: string = `${event.message}`;
      if (message.startsWith("Agent reached maximum")) {
        // We set the agent state to paused here - if the user clicks resume, it auto updates the max iterations
        send(generateAgentStateChangeEvent(AgentState.PAUSED));
      }
    }

    if (isErrorObservation(event)) {
      dispatch(
        addErrorMessage({
          id: event.extras?.error_id,
          message: event.message,
        }),
      );
    }

    // Handle agent mode changes
    // Handle agent delegation events
    if (
      "action" in event &&
      event.action === ActionType.DELEGATE &&
      "args" in event &&
      typeof event.args === "object" &&
      event.args !== null &&
      "agent" in event.args
    ) {
      // A delegation is starting
      const agentType = event.args.agent as string;
      dispatch(setDelegationState(true));
      dispatch(setAgentType(agentType));

      // Show notification
      if (agentType === "ReadOnlyAgent") {
        displaySuccessToast(t(I18nKey.AGENT$MODE_READ_ONLY));
      }
    }
    // Handle agent delegate observation (delegation ended)
    else if (
      "observation" in event &&
      event.observation === "delegate" &&
      "data" in event &&
      typeof event.data === "object" &&
      event.data !== null &&
      "status" in event.data &&
      event.data.status === "finished"
    ) {
      // Delegation has ended, returning to parent agent
      dispatch(setDelegationState(false));
      dispatch(setAgentType("CodeActAgent")); // Reset to default agent

      // Show notification
      displaySuccessToast(t(I18nKey.AGENT$MODE_EXECUTE));
    }
  }, [events.length, dispatch, send, t]);
};
