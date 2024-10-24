import React from "react";
import ArrowSendIcon from "#/assets/arrow-send.svg?react";
import { cn } from "#/utils/utils";

/**
 * Adjust the height of a textarea element based on its content
 * @param textareaRef The textarea element ref
 * @param maxRows The maximum number of rows to display
 */
const adjustHeight = (
  textareaRef: React.RefObject<HTMLTextAreaElement>,
  maxRows = 4,
) => {
  const textarea = textareaRef?.current;

  if (textarea) {
    // Calculate based on line height and max lines
    const lineHeight = parseInt(
      window.getComputedStyle(textarea).lineHeight,
      10,
    );

    textarea.style.height = "auto"; // Reset to auto to recalculate scroll height
    const { scrollHeight } = textarea;

    const maxHeight = lineHeight * maxRows;

    textarea.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
  }
};

interface ChatInputProps {
  name?: string;
  disabled?: boolean;
  placeholder?: string;
  showSubmitButton?: boolean;
  value?: string;
  maxRows?: number;
  onSubmit: (message: string) => void;
  onChange?: (message: string) => void;
  className?: React.HTMLAttributes<HTMLDivElement>["className"];
}

export function ChatInput({
  name,
  disabled,
  placeholder,
  showSubmitButton = true,
  value,
  maxRows,
  onSubmit,
  onChange,
  className,
}: ChatInputProps) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  const [text, setText] = React.useState("");

  React.useEffect(() => {
    adjustHeight(textareaRef, maxRows);
  }, [text, value]);

  const handleSubmitMessage = () => {
    if (textareaRef.current?.value) {
      onSubmit(textareaRef.current.value);
      textareaRef.current.value = "";
      setText("");
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmitMessage();
    }
  };

  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(event.target.value);
    onChange?.(event.target.value);
  };

  return (
    <div
      data-testid="chat-input"
      className="flex items-end justify-end grow gap-1"
    >
      <textarea
        ref={textareaRef}
        name={name}
        placeholder={placeholder}
        onKeyDown={handleKeyPress}
        onChange={handleChange}
        value={value}
        rows={1}
        className={cn(
          "grow text-sm self-center placeholder:text-neutral-400 text-white resize-none bg-transparent outline-none ring-0",
          className,
        )}
      />
      {showSubmitButton && (
        <button
          disabled={disabled}
          onClick={handleSubmitMessage}
          type="submit"
          className="border border-white rounded-lg w-6 h-6 hover:bg-neutral-500 flex items-center justify-center"
        >
          <ArrowSendIcon />
        </button>
      )}
    </div>
  );
}
