import React from "react";
import { useDispatch, useSelector } from "react-redux";
import toast from "react-hot-toast";
import posthog from "posthog-js";
import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";
import { ErrorObservation } from "#/types/core/observations";
import { addErrorMessage, addUserMessage } from "#/state/chatSlice";
import {
  getCloneRepoCommand,
  getGitHubTokenCommand,
} from "#/services/terminalService";
import {
  clearFiles,
  clearInitialQuery,
  clearSelectedRepository,
  setImportedProjectZip,
} from "#/state/initial-query-slice";
import store, { RootState } from "#/store";
import { createChatMessage } from "#/services/chatService";
import { isGitHubErrorReponse } from "#/api/github";
import { base64ToBlob } from "#/utils/base64-to-blob";
import { setCurrentAgentState } from "#/state/agentSlice";
import AgentState from "#/types/AgentState";
import { generateAgentStateChangeEvent } from "#/services/agentStateService";
import { useGitHubUser } from "#/hooks/query/use-github-user";
import { useUploadFiles } from "#/hooks/mutation/use-upload-files";
import { useAuth } from "#/context/auth-context";
import { useEndSession } from "#/hooks/use-end-session";
import { useUserPrefs } from "#/context/user-prefs-context";

interface ServerError {
  error: boolean | string;
  message: string;
  [key: string]: unknown;
}

const isServerError = (data: object): data is ServerError => "error" in data;

const isErrorObservation = (data: object): data is ErrorObservation =>
  "observation" in data && data.observation === "error";

export function EventHandler({ children }: React.PropsWithChildren) {
  const { setToken, gitHubToken } = useAuth();
  const { settings } = useUserPrefs();
  const { events, status, send } = useWsClient();
  const statusRef = React.useRef<WsClientProviderStatus | null>(null);
  const runtimeActive = status === WsClientProviderStatus.ACTIVE;
  const dispatch = useDispatch();
  const { files, importedProjectZip, initialQuery } = useSelector(
    (state: RootState) => state.initalQuery,
  );
  const endSession = useEndSession();

  // FIXME: Bad practice - should be handled with state
  const { selectedRepository } = useSelector(
    (state: RootState) => state.initalQuery,
  );

  const { data: user } = useGitHubUser();
  const { mutate: uploadFiles } = useUploadFiles();

  const sendInitialQuery = (query: string, base64Files: string[]) => {
    const timestamp = new Date().toISOString();
    send(createChatMessage(query, base64Files, timestamp));
  };
  const userId = React.useMemo(() => {
    if (user && !isGitHubErrorReponse(user)) return user.id;
    return null;
  }, [user]);

  React.useEffect(() => {
    if (!events.length) {
      return;
    }
    const event = events[events.length - 1];
    if (event.token && typeof event.token === "string") {
      setToken(event.token);
      return;
    }

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

  React.useEffect(() => {
    if (statusRef.current === status) {
      return; // This is a check because of strict mode - if the status did not change, don't do anything
    }
    statusRef.current = status;

    if (status === WsClientProviderStatus.ACTIVE) {
      let additionalInfo = "";
      if (gitHubToken && selectedRepository) {
        send(getCloneRepoCommand(gitHubToken, selectedRepository));
        additionalInfo = `Repository ${selectedRepository} has been cloned to /workspace. Please check the /workspace for files.`;
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
        dispatch(clearInitialQuery()); // reset initial query
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
    if (runtimeActive && userId && gitHubToken) {
      // Export if the user valid, this could happen mid-session so it is handled here
      send(getGitHubTokenCommand(gitHubToken));
    }
  }, [userId, gitHubToken, runtimeActive]);

  React.useEffect(() => {
    if (runtimeActive && importedProjectZip) {
      const blob = base64ToBlob(importedProjectZip);
      const file = new File([blob], "imported-project.zip", {
        type: blob.type,
      });
      uploadFiles(
        { files: [file] },
        {
          onError: () => {
            toast.error("Failed to upload project files.");
          },
        },
      );
      dispatch(setImportedProjectZip(null));
    }
  }, [runtimeActive, importedProjectZip]);

  React.useEffect(() => {
    if (settings.LLM_API_KEY) {
      posthog.capture("user_activated");
    }
  }, [settings.LLM_API_KEY]);

  return children;
}
