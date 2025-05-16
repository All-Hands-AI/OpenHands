import React from "react";
import { useWsClient } from "#/context/ws-client-provider";
import { generateAgentStateChangeEvent } from "#/services/agent-state-service";
import { AgentState } from "#/types/agent-state";
import { displayErrorToast } from "#/utils/custom-toast-handlers";

interface ServerError {
  error: boolean | string;
  message: string;
  [key: string]: unknown;
}

const isServerError = (data: object): data is ServerError => "error" in data;

export const useHandleWSEvents = () => {
  const { events, send } = useWsClient();

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
  }, [events.length]);
};
