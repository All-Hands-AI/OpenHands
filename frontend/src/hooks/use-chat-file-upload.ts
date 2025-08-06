import React from "react";
import { useSelector, useDispatch } from "react-redux";
import { isFileImage } from "#/utils/is-file-image";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { validateFiles } from "#/utils/file-validation";
import { RootState } from "#/store";
import {
  addImages,
  addFiles,
  removeImage,
  removeFile,
  clearImages,
  clearFiles,
  clearAllFiles,
} from "#/state/conversation-slice";

interface UseChatFileUploadReturn {
  images: File[];
  files: File[];
  handleUpload: (selectedFiles: File[]) => void;
  handleRemoveFile: (index: number) => void;
  handleRemoveImage: (index: number) => void;
  clearFiles: () => void;
  clearImages: () => void;
  clearAll: () => void;
}

export function useChatFileUpload(): UseChatFileUploadReturn {
  const dispatch = useDispatch();
  const images = useSelector((state: RootState) => state.conversation.images);
  const files = useSelector((state: RootState) => state.conversation.files);

  const handleUpload = React.useCallback(
    (selectedFiles: File[]) => {
      // Validate files before adding them
      const validation = validateFiles(selectedFiles, [...images, ...files]);

      if (!validation.isValid) {
        displayErrorToast(`Error: ${validation.errorMessage}`);
        return; // Don't add any files if validation fails
      }

      // Filter valid files by type
      const validFiles = selectedFiles.filter((f) => !isFileImage(f));
      const validImages = selectedFiles.filter((f) => isFileImage(f));

      if (validFiles.length > 0) {
        dispatch(addFiles(validFiles));
      }
      if (validImages.length > 0) {
        dispatch(addImages(validImages));
      }
    },
    [dispatch, images, files],
  );

  const handleRemoveFile = React.useCallback(
    (index: number) => {
      dispatch(removeFile(index));
    },
    [dispatch],
  );

  const handleRemoveImage = React.useCallback(
    (index: number) => {
      dispatch(removeImage(index));
    },
    [dispatch],
  );

  const clearFilesFn = React.useCallback(() => {
    dispatch(clearFiles());
  }, [dispatch]);

  const clearImagesFn = React.useCallback(() => {
    dispatch(clearImages());
  }, [dispatch]);

  const clearAllFn = React.useCallback(() => {
    dispatch(clearAllFiles());
  }, [dispatch]);

  return {
    images,
    files,
    handleUpload,
    handleRemoveFile,
    handleRemoveImage,
    clearFiles: clearFilesFn,
    clearImages: clearImagesFn,
    clearAll: clearAllFn,
  };
}
