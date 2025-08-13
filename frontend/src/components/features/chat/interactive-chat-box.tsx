import { useSelector, useDispatch } from "react-redux";
import { isFileImage } from "#/utils/is-file-image";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { validateFiles } from "#/utils/file-validation";
import { CustomChatInput } from "./custom-chat-input";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { GitControlBar } from "./git-control-bar";
import {
  addImages,
  addFiles,
  clearAllFiles,
  addFileLoading,
  removeFileLoading,
  addImageLoading,
  removeImageLoading,
} from "#/state/conversation-slice";
import { processFiles, processImages } from "#/utils/file-processing";

interface InteractiveChatBoxProps {
  onSubmit: (message: string, images: File[], files: File[]) => void;
  onStop: () => void;
  value?: string;
  isWaitingForUserInput: boolean;
  hasSubstantiveAgentActions: boolean;
  optimisticUserMessage: boolean;
}

export function InteractiveChatBox({
  onSubmit,
  onStop,
  value,
  isWaitingForUserInput,
  hasSubstantiveAgentActions,
  optimisticUserMessage,
}: InteractiveChatBoxProps) {
  const dispatch = useDispatch();
  const curAgentState = useSelector(
    (state: RootState) => state.agent.curAgentState,
  );
  const images = useSelector((state: RootState) => state.conversation.images);
  const files = useSelector((state: RootState) => state.conversation.files);
  const { data: conversation } = useActiveConversation();

  // Helper function to validate and filter files
  const validateAndFilterFiles = (selectedFiles: File[]) => {
    const validation = validateFiles(selectedFiles, [...images, ...files]);

    if (!validation.isValid) {
      displayErrorToast(`Error: ${validation.errorMessage}`);
      return null;
    }

    const validFiles = selectedFiles.filter((f) => !isFileImage(f));
    const validImages = selectedFiles.filter((f) => isFileImage(f));

    return { validFiles, validImages };
  };

  // Helper function to show loading indicators for files
  const showLoadingIndicators = (validFiles: File[], validImages: File[]) => {
    validFiles.forEach((file) => dispatch(addFileLoading(file.name)));
    validImages.forEach((image) => dispatch(addImageLoading(image.name)));
  };

  // Helper function to handle successful file processing results
  const handleSuccessfulFiles = (fileResults: { successful: File[] }) => {
    if (fileResults.successful.length > 0) {
      dispatch(addFiles(fileResults.successful));
      fileResults.successful.forEach((file) =>
        dispatch(removeFileLoading(file.name)),
      );
    }
  };

  // Helper function to handle successful image processing results
  const handleSuccessfulImages = (imageResults: { successful: File[] }) => {
    if (imageResults.successful.length > 0) {
      dispatch(addImages(imageResults.successful));
      imageResults.successful.forEach((image) =>
        dispatch(removeImageLoading(image.name)),
      );
    }
  };

  // Helper function to handle failed file processing results
  const handleFailedFiles = (
    fileResults: { failed: { file: File; error: Error }[] },
    imageResults: { failed: { file: File; error: Error }[] },
  ) => {
    fileResults.failed.forEach(({ file, error }) => {
      dispatch(removeFileLoading(file.name));
      displayErrorToast(
        `Failed to process file ${file.name}: ${error.message}`,
      );
    });

    imageResults.failed.forEach(({ file, error }) => {
      dispatch(removeImageLoading(file.name));
      displayErrorToast(
        `Failed to process image ${file.name}: ${error.message}`,
      );
    });
  };

  // Helper function to clear loading states on error
  const clearLoadingStates = (validFiles: File[], validImages: File[]) => {
    validFiles.forEach((file) => dispatch(removeFileLoading(file.name)));
    validImages.forEach((image) => dispatch(removeImageLoading(image.name)));
  };

  const handleUpload = async (selectedFiles: File[]) => {
    // Step 1: Validate and filter files
    const result = validateAndFilterFiles(selectedFiles);
    if (!result) return;

    const { validFiles, validImages } = result;

    // Step 2: Show loading indicators immediately
    showLoadingIndicators(validFiles, validImages);

    // Step 3: Process files using REAL FileReader
    try {
      const [fileResults, imageResults] = await Promise.all([
        processFiles(validFiles),
        processImages(validImages),
      ]);

      // Step 4: Handle successful results
      handleSuccessfulFiles(fileResults);
      handleSuccessfulImages(imageResults);

      // Step 5: Handle failed results
      handleFailedFiles(fileResults, imageResults);
    } catch (error) {
      // Clear loading states and show error
      clearLoadingStates(validFiles, validImages);
      displayErrorToast("An unexpected error occurred while processing files");
    }
  };

  const handleSubmit = (message: string) => {
    onSubmit(message, images, files);
    dispatch(clearAllFiles());
  };

  const handleSuggestionsClick = (suggestion: string) => {
    handleSubmit(suggestion);
  };

  const isDisabled =
    curAgentState === AgentState.LOADING ||
    curAgentState === AgentState.AWAITING_USER_CONFIRMATION;

  return (
    <div data-testid="interactive-chat-box">
      <CustomChatInput
        disabled={isDisabled}
        onSubmit={handleSubmit}
        onStop={onStop}
        onFilesPaste={handleUpload}
        value={value}
        conversationStatus={conversation?.status || null}
      />
      <div className="mt-4">
        <GitControlBar
          onSuggestionsClick={handleSuggestionsClick}
          isWaitingForUserInput={isWaitingForUserInput}
          hasSubstantiveAgentActions={hasSubstantiveAgentActions}
          optimisticUserMessage={optimisticUserMessage}
        />
      </div>
    </div>
  );
}
