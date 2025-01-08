import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { useAuth } from "#/context/auth-context";
import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";
import { createChatMessage } from "#/services/chat-service";
import { setCurrentAgentState } from "#/state/agent-slice";
import { addUserMessage } from "#/state/chat-slice";
import { clearFiles, clearInitialQuery } from "#/state/initial-query-slice";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";

export const useWSStatusChange = () => {
  const { send, status } = useWsClient();
  const { gitHubToken } = useAuth();
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const dispatch = useDispatch();

  const statusRef = React.useRef<WsClientProviderStatus | null>(null);

  const { selectedRepository } = useSelector(
    (state: RootState) => state.initialQuery,
  );

  const { files, importedProjectZip, initialQuery } = useSelector(
    (state: RootState) => state.initialQuery,
  );

  const sendInitialQuery = (query: string, base64Files: string[]) => {
    const timestamp = new Date().toISOString();
    send(createChatMessage(query, base64Files, timestamp));
  };

  const dispatchInitialQuery = (query: string, additionalInfo: string) => {
    if (additionalInfo) {
      sendInitialQuery(`${query}\n\n[${additionalInfo}]`, files);
    } else {
      sendInitialQuery(query, files);
    }

    dispatch(clearFiles()); // reset selected files
    dispatch(clearInitialQuery()); // reset initial query
  };

  const handleAgentInit = () => {
    let additionalInfo = "";

    if (gitHubToken && selectedRepository) {
      additionalInfo = `Repository ${selectedRepository} has been cloned to /workspace. Please check the /workspace for files.`;
    } else if (importedProjectZip) {
      // if there's an uploaded project zip, add it to the chat
      additionalInfo =
        "Files have been uploaded. Please check the /workspace for files.";
    }

    if (initialQuery) {
      dispatchInitialQuery(initialQuery, additionalInfo);
    }
  };
  React.useEffect(() => {
    if (curAgentState === AgentState.INIT) {
      handleAgentInit();
    }
  }, [curAgentState]);

  React.useEffect(() => {
    if (statusRef.current === status) {
      return; // This is a check because of strict mode - if the status did not change, don't do anything
    }
    statusRef.current = status;

    if (status !== WsClientProviderStatus.DISCONNECTED && initialQuery) {
      dispatch(
        addUserMessage({
          content: initialQuery,
          imageUrls: files,
          timestamp: new Date().toISOString(),
          pending: true,
        }),
      );
    }

    if (status === WsClientProviderStatus.DISCONNECTED) {
      dispatch(setCurrentAgentState(AgentState.STOPPED));
    }
  }, [status]);
};
