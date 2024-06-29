import { Textarea } from "@nextui-org/react";
import React from "react";
import { useTranslation } from "react-i18next";
import { VscArrowUp } from "react-icons/vsc";
import { twMerge } from "tailwind-merge";
import { I18nKey } from "#/i18n/declaration";
import { useAgentState } from "#/hooks/useAgentState";
import AgentState from "#/types/AgentState";

interface ChatInputProps {
  disabled?: boolean;
  onSendMessage: (message: string) => void;
}

function ChatInput({ disabled = false, onSendMessage }: ChatInputProps) {
  const { curAgentState } = useAgentState();

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
      if (!disabled) {
        handleSendChatMessage();
      }
    }
  };

  return (
    <div className="w-full relative text-base flex">
      <Textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={onKeyPress}
        onCompositionStart={() => setIsComposing(true)}
        onCompositionEnd={() => setIsComposing(false)}
        placeholder={t(I18nKey.CHAT_INTERFACE$INPUT_PLACEHOLDER)}
        className="pb-3 px-3"
        classNames={{
          inputWrapper: "bg-bg-input border-border rounded-lg",
          input: twMerge(
            "pr-16",
            curAgentState === AgentState.AWAITING_USER_INPUT ||
              curAgentState === AgentState.FINISHED ||
              curAgentState === AgentState.INIT ||
              curAgentState === AgentState.STOPPED ||
              curAgentState === AgentState.ERROR
              ? "text-text-editor-active"
              : "text-text-editor-base",
          ),
        }}
        maxRows={10}
        minRows={1}
        variant="bordered"
      />

      <button
        type="button"
        onClick={handleSendChatMessage}
        disabled={disabled}
        className={twMerge(
          "bg-transparent border rounded-lg p-1 border-border hover:opacity-80 cursor-pointer select-none absolute right-5 bottom-[19px] transition active:bg-bg-light active:text-text-editor-active",
          disabled
            ? "cursor-not-allowed border-neutral-400 text-text-editor-base"
            : "hover:bg-bg-light",
        )}
        aria-label={t(I18nKey.CHAT_INTERFACE$TOOLTIP_SEND_MESSAGE)}
      >
        <VscArrowUp />
      </button>
    </div>
  );
}

export default ChatInput;
