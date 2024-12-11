import React from "react";
import toast from "react-hot-toast";
import { useDispatch, useSelector } from "react-redux";
import { isGitHubErrorReponse } from "#/api/github";
import { useAuth } from "#/context/auth-context";
import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";
import { getGitHubTokenCommand } from "#/services/terminal-service";
import { setImportedProjectZip } from "#/state/initial-query-slice";
import { RootState } from "#/store";
import { base64ToBlob } from "#/utils/base64-to-blob";
import { useUploadFiles } from "../../../hooks/mutation/use-upload-files";
import { useGitHubUser } from "../../../hooks/query/use-github-user";

export const useHandleRuntimeActive = () => {
  const { gitHubToken } = useAuth();
  const { status, send } = useWsClient();

  const dispatch = useDispatch();

  const { data: user } = useGitHubUser();
  const { mutate: uploadFiles } = useUploadFiles();

  const runtimeActive = status === WsClientProviderStatus.ACTIVE;

  const { importedProjectZip } = useSelector(
    (state: RootState) => state.initalQuery,
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
