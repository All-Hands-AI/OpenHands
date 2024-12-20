import React from "react";
import toast from "react-hot-toast";
import { useDispatch } from "react-redux";
import { useWsClient } from "#/context/ws-client-provider";
import { generateAgentStateChangeEvent } from "#/services/agent-state-service";
import { addErrorMessage } from "#/state/chat-slice";
import { AgentState } from "#/types/agent-state";
import { ErrorObservation } from "#/types/core/observations";
import { useEndSession } from "../../../hooks/use-end-session";

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
  const endSession = useEndSession();
  const dispatch = useDispatch();

  React.useEffect(() => {
    if (!events.length) {
      return;
    }
    const event = events[events.length - 1];

    if (isServerError(event)) {
      if (event.error_code === 401) {
        toast.error("Session expired.");
        endSession();
        return;
      }

      if (typeof event.error === "string") {
        toast.error(event.error);
      } else {
        toast.error(event.message);
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
  }, [events.length]);
};
