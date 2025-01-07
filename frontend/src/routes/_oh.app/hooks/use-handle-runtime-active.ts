import React from "react";
import toast from "react-hot-toast";
import { useDispatch, useSelector } from "react-redux";
import { useAuth } from "#/context/auth-context";
import { useWsClient } from "#/context/ws-client-provider";
import { getGitHubTokenCommand } from "#/services/terminal-service";
import { setImportedProjectZip } from "#/state/initial-query-slice";
import { RootState } from "#/store";
import { base64ToBlob } from "#/utils/base64-to-blob";
import { useUploadFiles } from "../../../hooks/mutation/use-upload-files";
import { useGitHubUser } from "../../../hooks/query/use-github-user";
import { isGitHubErrorReponse } from "#/api/github-axios-instance";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";

export const useHandleRuntimeActive = () => {
  const { gitHubToken } = useAuth();
  const { send } = useWsClient();

  const dispatch = useDispatch();

  const { data: user } = useGitHubUser();
  const { mutate: uploadFiles } = useUploadFiles();
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const runtimeActive = !RUNTIME_INACTIVE_STATES.includes(curAgentState);

  const { importedProjectZip } = useSelector(
    (state: RootState) => state.initialQuery,
  );

  const userId = React.useMemo(() => {
    if (user && !isGitHubErrorReponse(user)) return user.id;
    return null;
  }, [user]);

  const handleUploadFiles = (zip: string) => {
    const blob = base64ToBlob(zip);
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
  };

  React.useEffect(() => {
    if (runtimeActive && userId && gitHubToken) {
      // Export if the user valid, this could happen mid-session so it is handled here
      send(getGitHubTokenCommand(gitHubToken));
    }
  }, [userId, gitHubToken, runtimeActive]);

  React.useEffect(() => {
    if (runtimeActive && importedProjectZip) {
      handleUploadFiles(importedProjectZip);
    }
  }, [runtimeActive, importedProjectZip]);
};
