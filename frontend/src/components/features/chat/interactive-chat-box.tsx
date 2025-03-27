import React from "react";
import { ChatInput } from "./chat-input";
import { cn } from "#/utils/utils";
import { ImageCarousel } from "../images/image-carousel";
import { UploadImageInput } from "../images/upload-image-input";

interface InteractiveChatBoxProps {
  isDisabled?: boolean;
  mode?: "stop" | "submit";
  onSubmit: (message: string, images: File[]) => void;
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

  const [nonImageFiles, setNonImageFiles] = React.useState<File[]>([]);

  const handleUpload = (files: File[]) => {
    const imageFiles = files.filter((file) => file.type.startsWith("image/"));
    const otherFiles = files.filter((file) => !file.type.startsWith("image/"));

    setImages((prevImages) => [...prevImages, ...imageFiles]);

    if (otherFiles.length > 0) {
      setNonImageFiles((prevFiles) => [...prevFiles, ...otherFiles]);

      // Create a message mentioning the uploaded files
      const fileNames = otherFiles.map((file) => file.name).join(", ");
      const fileMessage = `I've uploaded the following file(s): ${fileNames}`;

      // Set the message to the textarea
      onChange?.(fileMessage);
    }
  };

  const handleRemoveImage = (index: number) => {
    setImages((prevImages) => {
      const newImages = [...prevImages];
      newImages.splice(index, 1);
      return newImages;
    });
  };

  const handleSubmit = (message: string) => {
    // Combine both image and non-image files
    const allFiles = [...images, ...nonImageFiles];
    onSubmit(message, allFiles);
    setImages([]);
    setNonImageFiles([]);
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

      <div
        className={cn(
          "flex items-end gap-1",
          "bg-tertiary border border-neutral-600 rounded-lg px-2",
          "transition-colors duration-200",
          "hover:border-neutral-500 focus-within:border-neutral-500",
        )}
      >
        <UploadImageInput onUpload={handleUpload} acceptAll />
        <ChatInput
          disabled={isDisabled}
          button={mode}
          onChange={onChange}
          onSubmit={handleSubmit}
          onStop={onStop}
          value={value}
          onImagePaste={handleUpload}
          className="py-[10px]"
          buttonClassName="py-[10px]"
        />
      </div>
    </div>
  );
}
