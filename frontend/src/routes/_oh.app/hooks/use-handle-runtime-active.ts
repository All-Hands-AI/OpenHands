import React from "react";
import toast from "react-hot-toast";
import { useDispatch, useSelector } from "react-redux";
import { setImportedProjectZip } from "#/state/initial-query-slice";
import { RootState } from "#/store";
import { base64ToBlob } from "#/utils/base64-to-blob";
import { useUploadFiles } from "../../../hooks/mutation/use-upload-files";

import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";

export const useHandleRuntimeActive = () => {
  const dispatch = useDispatch();

  const { mutate: uploadFiles } = useUploadFiles();
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const runtimeActive = !RUNTIME_INACTIVE_STATES.includes(curAgentState);

  const { importedProjectZip } = useSelector(
    (state: RootState) => state.initialQuery,
  );

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
    if (runtimeActive && importedProjectZip) {
      handleUploadFiles(importedProjectZip);
    }
  }, [runtimeActive, importedProjectZip]);
};
