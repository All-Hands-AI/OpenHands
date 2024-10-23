import React from "react";
import ArrowSendIcon from "#/assets/arrow-send.svg?react";

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
  disabled?: boolean;
  placeholder?: string;
  onSubmit: (message: string) => void;
}

export function ChatInput({ disabled, placeholder, onSubmit }: ChatInputProps) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  const [value, setValue] = React.useState("");

  React.useEffect(() => {
    adjustHeight(textareaRef);
  }, [value]);

  const handleSubmitMessage = () => {
    if (textareaRef.current?.value) {
      onSubmit(textareaRef.current.value);
      textareaRef.current.value = "";
      setValue("");
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmitMessage();
    }
  };

  return (
    <div
      data-testid="chat-input"
      className="flex items-end justify-end grow gap-1"
    >
      <textarea
        ref={textareaRef}
        name="message"
        placeholder={placeholder}
        onKeyDown={handleKeyPress}
        onChange={(e) => setValue(e.target.value)}
        rows={1}
        className="grow text-sm self-center placeholder:text-neutral-400 text-white resize-none bg-transparent outline-none ring-0"
      />
      <button
        disabled={disabled}
        onClick={handleSubmitMessage}
        type="submit"
        className="border border-white rounded-lg w-6 h-6 hover:bg-neutral-500 flex items-center justify-center"
      >
        <ArrowSendIcon />
      </button>
    </div>
  );
}
