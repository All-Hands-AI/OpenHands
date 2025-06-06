import React from "react";
import { ChatInput } from "./chat-input";
import { cn } from "#/utils/utils";
import { ImageCarousel } from "../images/image-carousel";
import { UploadImageInput } from "../images/upload-image-input";
import { FileList } from "../files/file-list";
import { isFileImage } from "#/utils/is-file-image";

type SelectedFile = { file: File; id: string };

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
  const [files, setFiles] = React.useState<SelectedFile[]>([]);

  const handleUpload = (selectedFiles: File[]) => {
    setFiles((prevFiles) => [
      ...prevFiles,
      ...selectedFiles.map((file) => ({ file, id: crypto.randomUUID() })),
    ]);
  };

  const handleRemoveFile = (id: string) => {
    setFiles((prevFiles) => {
      const newFiles = [...prevFiles];
      const index = newFiles.findIndex((f) => f.id === id);
      newFiles.splice(index, 1);
      return newFiles;
    });
  };

  const images = files.filter((f) => isFileImage(f.file));
  const nonImageFiles = files.filter((f) => !isFileImage(f.file));

  const handleSubmit = (message: string) => {
    onSubmit(
      message,
      images.map((f) => f.file),
      nonImageFiles.map((f) => f.file),
    );
    setFiles([]);
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
          images={images.map((image) => ({
            id: image.id,
            src: URL.createObjectURL(image.file),
          }))}
          onRemove={handleRemoveFile}
        />
      )}
      {nonImageFiles.length > 0 && (
        <FileList
          files={nonImageFiles.map((f) => ({
            filename: f.file.name,
            id: f.id,
          }))}
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
