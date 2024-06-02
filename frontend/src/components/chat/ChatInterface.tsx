import React, { useRef, useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { IoMdChatbubbles } from "react-icons/io";
import { RiArrowRightDoubleLine } from "react-icons/ri";
import { useTranslation } from "react-i18next";
import { twMerge } from "tailwind-merge";
import { VscArrowDown } from "react-icons/vsc";
import { FaRegThumbsDown, FaRegThumbsUp } from "react-icons/fa";
import ChatInput from "./ChatInput";
import Chat from "./Chat";
import { RootState } from "#/store";
import AgentState from "#/types/AgentState";
import { sendChatMessage } from "#/services/chatService";
import { addUserMessage, addAssistantMessage } from "#/state/chatSlice";
import { I18nKey } from "#/i18n/declaration";
import { useScrollToBottom } from "#/hooks/useScrollToBottom";
import FeedbackModal from "#/components/modals/feedback/FeedbackModal";
import Session from "#/services/session";
import { getToken } from "#/services/auth";
import toast from "#/utils/toast";
import { removeApiKey } from "#/utils/utils";
import { Feedback, sendFeedback } from "#/services/feedbackService";
import { useDisclosure } from "@nextui-org/react";

interface ScrollButtonProps {
  onClick: () => void;
  icon: JSX.Element;
  label: string;
  disabled?: boolean;
}

function ScrollButton({
  onClick,
  icon,
  label,
  disabled = false,
}: ScrollButtonProps): JSX.Element {
  return (
    <button
      type="button"
      className="relative border-1 text-xs rounded px-2 py-1 border-neutral-600 bg-neutral-700 cursor-pointer select-none"
      onClick={onClick}
      disabled={disabled}
    >
      <div className="flex items-center">
        {icon} <span className="inline-block">{label}</span>
      </div>
    </button>
  );
}

function ChatInterface() {
  const dispatch = useDispatch();
  const { t } = useTranslation();
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [feedback, setFeedback] = React.useState<Feedback>({} as Feedback);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const curAgentState = useSelector((state: RootState) => state.agentState);
  const messages = useSelector((state: RootState) => state.chat.messages);
  const hitBottom = useScrollToBottom(chatContainerRef);

  const {
    isOpen: feedbackModalIsOpen,
    onOpen: onFeedbackModalOpen,
    onOpenChange: onFeedbackModalOpenChange,
  } = useDisclosure();

  const handleSendMessage = async (message: string) => {
    if (!message.trim()) return;
    dispatch(addUserMessage(message));
    try {
      const response = await sendChatMessage(message);
      dispatch(addAssistantMessage(response));
    } catch (error) {
      toast.error(t(I18nKey.CHAT_INTERFACE));
    }
  };

  const handleSendContinueMsg = async () => {
    try {
      const response = await sendChatMessage("continue");
      dispatch(addAssistantMessage(response));
    } catch (error) {
      toast.error(t(I18nKey.CHAT_INTERFACE));
    }
  };

  const scrollDomToBottom = () => {
    chatContainerRef.current?.scrollTo({
      top: chatContainerRef.current.scrollHeight,
      behavior: "smooth",
    });
  };

  const openFeedback = (polarity: "positive" | "negative") => {
    setFeedbackPolarity(polarity);
    onFeedbackModalOpen();
  };

  const handleDialogClose = async (shared: boolean) => {
    setDialogOpen(false);
    if (shared) {
      setFeedbackLoading(true);
      try {
        const feedbackData: FeedbackData = {
          messages,
          makePublic,
        };
        await sendFeedback(feedbackData);
        setFeedbackShared(true);
        toast.success(t(I18nKey.CHAT_INTERFACE));
      } catch (error) {
        toast.error(t(I18nKey.CHAT_INTERFACE));
      } finally {
        setFeedbackLoading(false);
      }
    }
  };

  return (
    <div className="relative h-full flex flex-col">
      <div className="flex-1 overflow-y-auto" ref={chatContainerRef}>
        <Chat />
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
            <ScrollButton
              onClick={scrollDomToBottom}
              icon={<VscArrowDown className="inline mr-2 w-3 h-3" />}
              label={t(I18nKey.CHAT_INTERFACE$TO_BOTTOM)}
            />}
          {curAgentState === AgentState.AWAITING_USER_INPUT &&
            hitBottom &&
            <ScrollButton
              onClick={handleSendContinueMsg}
              icon={<RiArrowRightDoubleLine className="inline mr-2 w-3 h-3" />}
              label={t(I18nKey.CHAT_INTERFACE$INPUT_CONTINUE_MESSAGE)}
            />}
        </div>

        {!feedbackShared && messages.length > 3 && (
          <div className="flex justify-start gap-2 p-2">
            <ScrollButton
              disabled={feedbackLoading}
              onClick={() => openFeedback("positive")}
              icon={<FaRegThumbsUp className="inline mr-2 w-3 h-3" />}
              label=""
            />
            <ScrollButton
              disabled={feedbackLoading}
              onClick={() => openFeedback("negative")}
              icon={<FaRegThumbsDown className="inline mr-2 w-3 h-3" />}
              label=""
            />
          </div>
        )}
      </div>

      <ChatInput
        disabled={curAgentState === AgentState.LOADING}
        onSendMessage={handleSendMessage}
      />
      <FeedbackModal
        feedback={feedback}
        isOpen={feedbackModalIsOpen}
        onOpenChange={onFeedbackModalOpenChange}
      />
    </div>
  );
}

export default ChatInterface;
