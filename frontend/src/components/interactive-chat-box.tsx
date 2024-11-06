import React from "react";
import { UploadImageInput } from "./upload-image-input";
import { ChatInput } from "./chat-input";
import { cn } from "#/utils/utils";
import { ImageCarousel } from "./image-carousel";

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
          "bg-neutral-700 border border-neutral-600 rounded-lg px-2 py-[10px]",
          "transition-colors duration-200",
          "hover:border-neutral-500 focus-within:border-neutral-500",
          "group relative",
          "before:pointer-events-none before:absolute before:inset-0 before:rounded-lg before:transition-colors",
          "before:border-2 before:border-dashed before:border-transparent",
          "[&:has(*:focus-within)]:before:border-neutral-500/50",
          "[&:has(*[data-dragging-over='true'])]:before:border-neutral-500/50",
        )}
      >
        <UploadImageInput onUpload={handleUpload} />
        <ChatInput
          disabled={isDisabled}
          button={mode}
          placeholder="What do you want to build?"
          onChange={onChange}
          onSubmit={handleSubmit}
          onStop={onStop}
          value={value}
          onImagePaste={handleUpload}
        />
      </div>
    </div>
  );
}
