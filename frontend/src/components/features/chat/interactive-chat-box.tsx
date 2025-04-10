import { cn } from "#/utils/utils";
import React from "react";
import { ImageCarousel } from "../images/image-carousel";
import { UploadImageInput } from "../images/upload-image-input";
import { ChatInput } from "./chat-input";

interface InteractiveChatBoxProps {
  isDisabled?: boolean;
  mode?: "stop" | "submit";
  onSubmit: (message: string, images: File[]) => void;
  onStop: () => void;
  value?: string;
  onChange?: (message: string) => void;
  className?: string; // Add className to the interface
}

export function InteractiveChatBox({
  isDisabled,
  mode = "submit",
  onSubmit,
  onStop,
  value,
  onChange,
  className, // Destructure className
}: InteractiveChatBoxProps) {
  const [images, setImages] = React.useState<File[]>([]);

  const handleUpload = (files: File[]) => {
    setImages((prevImages) => [...prevImages, ...files]);
  };

  const handleRemoveImage = (index: number) => {
    setImages((prevImages) => {
      const newImages = [...prevImages];
      newImages.splice(index, 1);
      return newImages;
    });
  };

  const handleSubmit = (message: string) => {
    onSubmit(message, images);
    setImages([]);
    if (message) {
      onChange?.("");
    }
  };

  return (
    <div
      data-testid="interactive-chat-box"
      className={cn("flex flex-col gap-[10px]", className)} // Apply className using cn utility
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
          "flex items-center gap-1",
          "rounded-xl px-2",
          "transition-colors duration-200 bg-gray-500",
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
          onImagePaste={handleUpload}
          className="py-[10px]"
          buttonClassName="py-[10px]"
        />
      </div>
    </div>
  );
}