import { useSelector } from "react-redux";
import React from "react";
import { isFileImage } from "#/utils/is-file-image";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { validateFiles } from "#/utils/file-validation";
import { CustomChatInput } from "./custom-chat-input";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";
import { ImageCarousel } from "../images/image-carousel";
import { FileList } from "../files/file-list";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";

interface InteractiveChatBoxProps {
  onSubmit: (message: string, images: File[], files: File[]) => void;
  onStop: () => void;
  value?: string;
}

export function InteractiveChatBox({
  onSubmit,
  onStop,
  value,
}: InteractiveChatBoxProps) {
  const curAgentState = useSelector(
    (state: RootState) => state.agent.curAgentState,
  );
  const { data: conversation } = useActiveConversation();

  const [images, setImages] = React.useState<File[]>([]);
  const [files, setFiles] = React.useState<File[]>([]);

  const handleUpload = (selectedFiles: File[]) => {
    // Validate files before adding them
    const validation = validateFiles(selectedFiles, [...images, ...files]);

    if (!validation.isValid) {
      displayErrorToast(`Error: ${validation.errorMessage}`);
      return; // Don't add any files if validation fails
    }

    // Filter valid files by type
    const validFiles = selectedFiles.filter((f) => !isFileImage(f));
    const validImages = selectedFiles.filter((f) => isFileImage(f));

    setFiles((prevFiles) => [...prevFiles, ...validFiles]);
    setImages((prevImages) => [...prevImages, ...validImages]);
  };

  const removeElementByIndex = (array: Array<File>, index: number) => {
    const newArray = [...array];
    newArray.splice(index, 1);
    return newArray;
  };

  const handleRemoveFile = (index: number) => {
    setFiles(removeElementByIndex(files, index));
  };
  const handleRemoveImage = (index: number) => {
    setImages(removeElementByIndex(images, index));
  };

  const handleSubmit = (message: string) => {
    onSubmit(message, images, files);
    setFiles([]);
    setImages([]);
  };

  const isDisabled =
    curAgentState === AgentState.LOADING ||
    curAgentState === AgentState.AWAITING_USER_CONFIRMATION;

  return (
    <div data-testid="interactive-chat-box">
      {images.length > 0 && (
        <ImageCarousel
          size="small"
          images={images.map((image) => URL.createObjectURL(image))}
          onRemove={handleRemoveImage}
        />
      )}
      {files.length > 0 && (
        <FileList
          files={files.map((f) => f.name)}
          onRemove={handleRemoveFile}
        />
      )}
      <CustomChatInput
        disabled={isDisabled}
        onSubmit={handleSubmit}
        onStop={onStop}
        onFilesPaste={handleUpload}
        value={value}
        conversationStatus={conversation?.status || null}
      />
    </div>
  );
}
