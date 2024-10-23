import React from "react";
import { ImagePreview } from "./image-preview";
import { UploadImageInput } from "./upload-image-input";
import { ChatInput } from "./chat-input";
import { cn } from "#/utils/utils";

interface InteractiveChatBoxProps {
  isDisabled?: boolean;
  onSubmit: (message: string, images: File[]) => void;
}

export function InteractiveChatBox({
  isDisabled,
  onSubmit,
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
        <div className="flex gap-2 overflow-x-scroll">
          {images.map((image, index) => (
            <ImagePreview
              key={index}
              src={URL.createObjectURL(image)}
              onRemove={() => handleRemoveImage(index)}
            />
          ))}
        </div>
      )}

      <div
        className={cn(
          "flex items-end gap-1",
          "bg-neutral-700 border border-neutral-600 rounded-lg px-2 py-[10px]",
        )}
      >
        <UploadImageInput onUpload={handleUpload} />
        <ChatInput
          disabled={isDisabled}
          placeholder="What do you want to build?"
          onSubmit={handleSubmit}
        />
      </div>
    </div>
  );
}
