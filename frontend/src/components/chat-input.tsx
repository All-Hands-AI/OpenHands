import React from "react";
import { cn } from "#/utils/utils";
import ArrowSendIcon from "#/assets/arrow-send.svg?react";

interface ChatInputProps {
  disabled?: boolean;
  placeholder?: string;
  onSubmit: (message: string) => void;
}

export function ChatInput({ disabled, placeholder, onSubmit }: ChatInputProps) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  const [isFocused, setIsFocused] = React.useState(false);

  const handleSubmitMessage = () => {
    if (textareaRef.current?.value) {
      onSubmit(textareaRef.current.value);
      textareaRef.current.value = "";
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmitMessage();
    }
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    handleSubmitMessage();
  };

  return (
    <form
      data-testid="chat-input"
      onSubmit={handleSubmit}
      className={cn(
        "flex items-center justify-end grow",
        // isFocused && "ring-2 ring-offset-2",
      )}
    >
      <textarea
        ref={textareaRef}
        name="message"
        placeholder={placeholder}
        onKeyDown={handleKeyPress}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        rows={1}
        className="grow text-sm placeholder:text-neutral-400 text-white resize-none bg-transparent outline-none ring-0"
      />
      <button
        disabled={disabled}
        type="submit"
        className="border border-white rounded-lg w-6 h-6 hover:bg-neutral-500 flex items-center justify-center"
      >
        <ArrowSendIcon />
      </button>
    </form>
  );
}
