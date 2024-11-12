import React from "react";
import TextareaAutosize from "react-textarea-autosize";
import ArrowSendIcon from "#/icons/arrow-send.svg?react";
import { cn } from "#/utils/utils";

interface ChatInputProps {
  name?: string;
  button?: "submit" | "stop";
  disabled?: boolean;
  placeholder?: string;
  showButton?: boolean;
  value?: string;
  maxRows?: number;
  onSubmit: (message: string) => void;
  onStop?: () => void;
  onChange?: (message: string) => void;
  onFocus?: () => void;
  onBlur?: () => void;
  onImagePaste?: (files: File[]) => void;
  className?: React.HTMLAttributes<HTMLDivElement>["className"];
}

export function ChatInput({
  name,
  button = "submit",
  disabled,
  placeholder,
  showButton = true,
  value,
  maxRows = 4,
  onSubmit,
  onStop,
  onChange,
  onFocus,
  onBlur,
  onImagePaste,
  className,
}: ChatInputProps) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  const [isDraggingOver, setIsDraggingOver] = React.useState(false);

  const handlePaste = (event: React.ClipboardEvent<HTMLTextAreaElement>) => {
    // Only handle paste if we have an image paste handler and there are files
    if (onImagePaste && event.clipboardData.files.length > 0) {
      const files = Array.from(event.clipboardData.files).filter((file) =>
        file.type.startsWith("image/"),
      );
      // Only prevent default if we found image files to handle
      if (files.length > 0) {
        event.preventDefault();
        onImagePaste(files);
      }
    }
    // For text paste, let the default behavior handle it
  };

  const handleDragOver = (event: React.DragEvent<HTMLTextAreaElement>) => {
    event.preventDefault();
    if (event.dataTransfer.types.includes("Files")) {
      setIsDraggingOver(true);
    }
  };

  const handleDragLeave = (event: React.DragEvent<HTMLTextAreaElement>) => {
    event.preventDefault();
    setIsDraggingOver(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLTextAreaElement>) => {
    event.preventDefault();
    setIsDraggingOver(false);
    if (onImagePaste && event.dataTransfer.files.length > 0) {
      const files = Array.from(event.dataTransfer.files).filter((file) =>
        file.type.startsWith("image/"),
      );
      if (files.length > 0) {
        onImagePaste(files);
      }
    }
  };

  const handleSubmitMessage = () => {
    if (textareaRef.current?.value) {
      onSubmit(textareaRef.current.value);
      textareaRef.current.value = "";
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey && !disabled) {
      event.preventDefault();
      handleSubmitMessage();
    }
  };

  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange?.(event.target.value);
  };

  return (
    <div
      data-testid="chat-input"
      className="flex items-end justify-end grow gap-1 min-h-6"
    >
      <TextareaAutosize
        ref={textareaRef}
        name={name}
        placeholder={placeholder}
        onKeyDown={handleKeyPress}
        onChange={handleChange}
        onFocus={onFocus}
        onBlur={onBlur}
        onPaste={handlePaste}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        value={value}
        minRows={1}
        maxRows={maxRows}
        data-dragging-over={isDraggingOver}
        className={cn(
          "grow text-sm self-center placeholder:text-neutral-400 text-white resize-none outline-none ring-0",
          "transition-all duration-200 ease-in-out",
          isDraggingOver
            ? "bg-neutral-600/50 rounded-lg px-2"
            : "bg-transparent",
          className,
        )}
      />
      {showButton && (
        <>
          {button === "submit" && (
            <button
              aria-label="Send"
              disabled={disabled}
              onClick={handleSubmitMessage}
              type="submit"
              className="border border-white rounded-lg w-6 h-6 hover:bg-neutral-500 focus:bg-neutral-500 flex items-center justify-center"
            >
              <ArrowSendIcon />
            </button>
          )}
          {button === "stop" && (
            <button
              data-testid="stop-button"
              aria-label="Stop"
              disabled={disabled}
              onClick={onStop}
              type="button"
              className="border border-white rounded-lg w-6 h-6 hover:bg-neutral-500 focus:bg-neutral-500 flex items-center justify-center"
            >
              <div className="w-[10px] h-[10px] bg-white" />
            </button>
          )}
        </>
      )}
    </div>
  );
}
