import React from "react";
import { ChatInput } from "./chat-input";
import { cn } from "#/utils/utils";
import { ImageCarousel } from "../images/image-carousel";
import { UploadImageInput } from "../images/upload-image-input";
import { FileList } from "../files/file-list";
import { isFileImage } from "#/utils/is-file-image";

interface InteractiveChatBoxProps {
  isDisabled?: boolean;
  mode?: "stop" | "submit";
  onSubmit: (message: string, images: File[], files: File[]) => void;
  onStop: () => void;
  value?: string;
  onChange?: (message: string) => void;
}

export function InteractiveChatBox({
  isDisabled,
  mode = "submit",
  onSubmit,
  onStop,
  value,
  onChange,
}: InteractiveChatBoxProps) {
  const [images, setImages] = React.useState<File[]>([]);
  const [files, setFiles] = React.useState<File[]>([]);

  const handleUpload = (selectedFiles: File[]) => {
    setFiles((prevFiles) => [
      ...prevFiles,
      ...selectedFiles.filter((f) => !isFileImage(f)),
    ]);
    setImages((prevImages) => [
      ...prevImages,
      ...selectedFiles.filter((f) => isFileImage(f)),
    ]);
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
    if (message) {
      onChange?.("");
    }
  };

  return (
    <div
      data-testid="interactive-chat-box"
      className="flex flex-col gap-[10px]"
    >
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

      <div
        className={cn(
          "flex items-end gap-1",
          "bg-tertiary border border-neutral-600 rounded-lg px-2",
          "transition-colors duration-200",
          "hover:border-neutral-500 focus-within:border-neutral-500",
        )}
      >
        <UploadImageInput onUpload={handleUpload} />
        <ChatInput
          disabled={isDisabled}
          button={mode}
          onChange={onChange}
          onSubmit={handleSubmit}
          onStop={onStop}
          value={value}
          onFilesPaste={handleUpload}
          className="py-[10px]"
          buttonClassName="py-[10px]"
        />
      </div>
    </div>
  );
}
