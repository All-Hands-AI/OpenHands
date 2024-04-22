import { Textarea } from "@nextui-org/react";
import React from "react";
import { useTranslation } from "react-i18next";
import { twMerge } from "tailwind-merge";
import { VscSend } from "react-icons/vsc";
import { I18nKey } from "#/i18n/declaration";

interface ChatInputProps {
  disabled?: boolean;
  onSendMessage: (message: string) => void;
}

function ChatInput({ disabled, onSendMessage }: ChatInputProps) {
  const { t } = useTranslation();

  const [message, setMessage] = React.useState("");
  // This is true when the user is typing in an IME (e.g., Chinese, Japanese)
  const [isComposing, setIsComposing] = React.useState(false);

  const handleSendChatMessage = () => {
    if (message.trim()) {
      onSendMessage(message);
      setMessage("");
    }
  };

  const onKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !event.shiftKey && !isComposing) {
      event.preventDefault(); // prevent a new line
      handleSendChatMessage();
    }
  };

  return (
    <div className="w-full relative text-base">
      <Textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        disabled={disabled}
        onKeyDown={onKeyPress}
        onCompositionStart={() => setIsComposing(true)}
        onCompositionEnd={() => setIsComposing(false)}
        placeholder={t(I18nKey.CHAT_INTERFACE$INPUT_PLACEHOLDER)}
        className="pt-2 pb-4 px-4"
        classNames={{
          inputWrapper: "bg-neutral-700",
          input: "pr-16 py-2",
        }}
        maxRows={10}
        minRows={1}
        variant="bordered"
      />

      <button
        type="button"
        onClick={handleSendChatMessage}
        className={twMerge(
          "bg-transparent border-none rounded py-2.5 px-5 hover:opacity-80 cursor-pointer select-none absolute right-5 bottom-6",
          disabled && "cursor-not-allowed opacity-80",
        )}
        aria-label="Send message"
      >
        <VscSend />
      </button>
    </div>
  );
}

ChatInput.defaultProps = {
  disabled: false,
};

export default ChatInput;
