import React, { useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import { IoMdChatbubbles } from "react-icons/io";
import { RiArrowRightDoubleLine } from "react-icons/ri";
import { useTranslation } from "react-i18next";
import { twMerge } from "tailwind-merge";
import { VscArrowDown } from "react-icons/vsc";
import ChatInput from "./ChatInput";
import Chat from "./Chat";
import { RootState } from "#/store";
import AgentState from "#/types/AgentState";
import { sendChatMessage } from "#/services/chatService";
import { addUserMessage } from "#/state/chatSlice";
import { I18nKey } from "#/i18n/declaration";
import { useScrollToBottom } from "#/hooks/useScrollToBottom";

interface ScrollButtonProps {
  onClick: () => void;
  icon: JSX.Element;
  label: string;
}

function ScrollButton({
  onClick,
  icon,
  label,
}: ScrollButtonProps): JSX.Element {
  return (
    <button
      type="button"
      className="relative border-1 text-xs rounded px-2 py-1 border-neutral-600 bg-neutral-700 cursor-pointer select-none"
      onClick={onClick}
    >
      <div className="flex items-center">
        {icon} <span className="inline-block">{label}</span>
      </div>
    </button>
  );
}

function ChatInterface() {
  const dispatch = useDispatch();
  const { messages } = useSelector((state: RootState) => state.chat);
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const handleSendMessage = (content: string) => {
    dispatch(addUserMessage(content));
    sendChatMessage(content);
  };

  const { t } = useTranslation();
  const handleSendContinueMsg = () => {
    handleSendMessage(t(I18nKey.CHAT_INTERFACE$INPUT_CONTINUE_MESSAGE));
  };

  const scrollRef = useRef<HTMLDivElement>(null);

  const { scrollDomToBottom, onChatBodyScroll, hitBottom } =
    useScrollToBottom(scrollRef);

  return (
    <div className="flex flex-col h-full bg-neutral-800">
      <div className="flex items-center gap-2 border-b border-neutral-600 text-sm px-4 py-2">
        <IoMdChatbubbles />
        Chat
      </div>
      <div className="flex-1 flex flex-col relative min-h-0">
        <div
          ref={scrollRef}
          className="overflow-y-auto p-3"
          onScroll={(e) => onChatBodyScroll(e.currentTarget)}
        >
          <Chat messages={messages} />
        </div>
        {/* Fade between messages and input */}
        <div
          className={twMerge(
            "absolute bottom-0 left-0 right-0",
            curAgentState === AgentState.AWAITING_USER_INPUT ? "h-10" : "h-4",
            "bg-gradient-to-b from-transparent to-neutral-800",
          )}
        />
      </div>

      <div className="relative">
        <div className="absolute bottom-2 left-0 right-0 flex items-center justify-center">
          {!hitBottom &&
            ScrollButton({
              onClick: scrollDomToBottom,
              icon: <VscArrowDown className="inline mr-2 w-3 h-3" />,
              label: t(I18nKey.CHAT_INTERFACE$TO_BOTTOM),
            })}
          {curAgentState === AgentState.AWAITING_USER_INPUT &&
            hitBottom &&
            ScrollButton({
              onClick: handleSendContinueMsg,
              icon: <RiArrowRightDoubleLine className="inline mr-2 w-3 h-3" />,
              label: t(I18nKey.CHAT_INTERFACE$INPUT_CONTINUE_MESSAGE),
            })}
        </div>
      </div>

      <ChatInput
        disabled={curAgentState === AgentState.LOADING}
        onSendMessage={handleSendMessage}
      />
    </div>
  );
}

export default ChatInterface;
