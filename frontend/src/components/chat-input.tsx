import React from "react";
import TextareaAutosize from "react-textarea-autosize";
import ArrowSendIcon from "#/assets/arrow-send.svg?react";
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
  className,
}: ChatInputProps) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

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
        value={value}
        minRows={1}
        maxRows={maxRows}
        className={cn(
          "grow text-sm self-center placeholder:text-neutral-400 text-white resize-none bg-transparent outline-none ring-0",
          "transition-[height] duration-200 ease-in-out",
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
