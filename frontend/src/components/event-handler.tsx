import React from "react";
import {
  useFetcher,
  useLoaderData,
  useRouteLoaderData,
} from "@remix-run/react";
import { useDispatch, useSelector } from "react-redux";
import toast from "react-hot-toast";

import posthog from "posthog-js";
import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";
import { ErrorObservation } from "#/types/core/observations";
import { addErrorMessage, addUserMessage } from "#/state/chatSlice";
import { handleAssistantMessage } from "#/services/actions";
import {
  getCloneRepoCommand,
  getGitHubTokenCommand,
} from "#/services/terminalService";
import {
  clearFiles,
  clearSelectedRepository,
  setImportedProjectZip,
} from "#/state/initial-query-slice";
import { clientLoader as appClientLoader } from "#/routes/_oh.app";
import store, { RootState } from "#/store";
import { createChatMessage } from "#/services/chatService";
import { clientLoader as rootClientLoader } from "#/routes/_oh";
import { isGitHubErrorReponse } from "#/api/github";
import OpenHands from "#/api/open-hands";
import { base64ToBlob } from "#/utils/base64-to-blob";
import { setCurrentAgentState } from "#/state/agentSlice";
import AgentState from "#/types/AgentState";
import { getSettings } from "#/services/settings";

interface ServerError {
  error: boolean | string;
  message: string;
  [key: string]: unknown;
}

const isServerError = (data: object): data is ServerError => "error" in data;

const isErrorObservation = (data: object): data is ErrorObservation =>
  "observation" in data && data.observation === "error";

export function EventHandler({ children }: React.PropsWithChildren) {
  const { events, status, send } = useWsClient();
  const statusRef = React.useRef<WsClientProviderStatus | null>(null);
  const runtimeActive = status === WsClientProviderStatus.ACTIVE;
  const fetcher = useFetcher();
  const dispatch = useDispatch();
  const { files, importedProjectZip } = useSelector(
    (state: RootState) => state.initalQuery,
  );
  const { ghToken, repo } = useLoaderData<typeof appClientLoader>();
  const initialQueryRef = React.useRef<string | null>(
    store.getState().initalQuery.initialQuery,
  );

  const sendInitialQuery = (query: string, base64Files: string[]) => {
    const timestamp = new Date().toISOString();
    send(createChatMessage(query, base64Files, timestamp));
  };
  const data = useRouteLoaderData<typeof rootClientLoader>("routes/_oh");
  const userId = React.useMemo(() => {
    if (data?.user && !isGitHubErrorReponse(data.user)) return data.user.id;
    return null;
  }, [data?.user]);
  const userSettings = getSettings();

  React.useEffect(() => {
    if (!events.length) {
      return;
    }
    const event = events[events.length - 1];
    if (event.token) {
      fetcher.submit({ token: event.token as string }, { method: "post" });
      return;
    }

    if (isServerError(event)) {
      if (event.error_code === 401) {
        toast.error("Session expired.");
        fetcher.submit({}, { method: "POST", action: "/end-session" });
        return;
      }

      if (typeof event.error === "string") {
        toast.error(event.error);
      } else {
        toast.error(event.message);
      }
      return;
    }

    if (isErrorObservation(event)) {
      dispatch(
        addErrorMessage({
          id: event.extras?.error_id,
          message: event.message,
        }),
      );
      return;
    }
    handleAssistantMessage(event);
  }, [events.length]);

  React.useEffect(() => {
    if (statusRef.current === status) {
      return; // This is a check because of strict mode - if the status did not change, don't do anything
    }
    statusRef.current = status;
    const initialQuery = initialQueryRef.current;

    if (status === WsClientProviderStatus.ACTIVE) {
      let additionalInfo = "";
      if (ghToken && repo) {
        send(getCloneRepoCommand(ghToken, repo));
        additionalInfo = `Repository ${repo} has been cloned to /workspace. Please check the /workspace for files.`;
        dispatch(clearSelectedRepository()); // reset selected repository; maybe better to move this to '/'?
      }
      // if there's an uploaded project zip, add it to the chat
      else if (importedProjectZip) {
        additionalInfo = `Files have been uploaded. Please check the /workspace for files.`;
      }

      if (initialQuery) {
        if (additionalInfo) {
          sendInitialQuery(`${initialQuery}\n\n[${additionalInfo}]`, files);
        } else {
          sendInitialQuery(initialQuery, files);
        }
        dispatch(clearFiles()); // reset selected files
        initialQueryRef.current = null;
      }
    }

    if (status === WsClientProviderStatus.OPENING && initialQuery) {
      dispatch(
        addUserMessage({
          content: initialQuery,
          imageUrls: files,
          timestamp: new Date().toISOString(),
        }),
      );
    }

    if (status === WsClientProviderStatus.STOPPED) {
      store.dispatch(setCurrentAgentState(AgentState.STOPPED));
    }
  }, [status]);

  React.useEffect(() => {
    if (runtimeActive && userId && ghToken) {
      // Export if the user valid, this could happen mid-session so it is handled here
      send(getGitHubTokenCommand(ghToken));
    }
  }, [userId, ghToken, runtimeActive]);

  React.useEffect(() => {
    (async () => {
      if (runtimeActive && importedProjectZip) {
        // upload files action
        try {
          const blob = base64ToBlob(importedProjectZip);
          const file = new File([blob], "imported-project.zip", {
            type: blob.type,
          });
          await OpenHands.uploadFiles([file]);
          dispatch(setImportedProjectZip(null));
        } catch (error) {
          toast.error("Failed to upload project files.");
        }
      }
    })();
  }, [runtimeActive, importedProjectZip]);

  React.useEffect(() => {
    if (userSettings.LLM_API_KEY) {
      posthog.capture("user_activated");
    }
  }, [userSettings.LLM_API_KEY]);

  return children;
}
