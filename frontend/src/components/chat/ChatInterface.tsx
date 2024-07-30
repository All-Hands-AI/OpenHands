import React, { useRef, useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { IoMdChatbubbles } from "react-icons/io";
import { RiArrowRightDoubleLine } from "react-icons/ri";
import { useTranslation } from "react-i18next";
import { VscArrowDown } from "react-icons/vsc";
import { FaRegThumbsDown, FaRegThumbsUp } from "react-icons/fa";
import { useDisclosure, Tooltip } from "@nextui-org/react";
import ChatInput from "./ChatInput";
import Chat from "./Chat";
import TypingIndicator from "./TypingIndicator";
import { RootState } from "#/store";
import AgentState from "#/types/AgentState";
import { sendChatMessage } from "#/services/chatService";
import { addUserMessage, addAssistantMessage } from "#/state/chatSlice";
import { I18nKey } from "#/i18n/declaration";
import { useScrollToBottom } from "#/hooks/useScrollToBottom";
import FeedbackModal from "../modals/feedback/FeedbackModal";
import beep from "#/utils/beep";

interface ScrollButtonProps {
  onClick: () => void;
  icon: JSX.Element;
  label: string;
  // eslint-disable-next-line react/require-default-props
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
  const { messages } = useSelector((state: RootState) => state.chat);
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const [feedbackPolarity, setFeedbackPolarity] = React.useState<
    "positive" | "negative"
  >("positive");
  const [feedbackShared, setFeedbackShared] = React.useState(0);
  const [autoMode, setAutoMode] = useState(false);

  const {
    isOpen: feedbackModalIsOpen,
    onOpen: onFeedbackModalOpen,
    onOpenChange: onFeedbackModalOpenChange,
  } = useDisclosure();

  const shareFeedback = async (polarity: "positive" | "negative") => {
    onFeedbackModalOpen();
    setFeedbackPolarity(polarity);
  };

  const handleSendMessage = (content: string, dispatchContent: string = "") => {
    dispatch(addUserMessage(dispatchContent || content));
    sendChatMessage(content);
  };

  const { t } = useTranslation();
  const handleSendContinueMsg = () => {
    handleSendMessage(t(I18nKey.CHAT_INTERFACE$INPUT_CONTINUE_MESSAGE));
  };

  const handleAutoMsg = () => {
    handleSendMessage(
      t(I18nKey.CHAT_INTERFACE$AUTO_MESSAGE),
      t(I18nKey.CHAT_INTERFACE$INPUT_AUTO_MESSAGE),
    );
  };

  const scrollRef = useRef<HTMLDivElement>(null);

  const { scrollDomToBottom, onChatBodyScroll, hitBottom } =
    useScrollToBottom(scrollRef);

  useEffect(() => {
    if (curAgentState === AgentState.INIT && messages.length === 0) {
      dispatch(addAssistantMessage(t(I18nKey.CHAT_INTERFACE$INITIAL_MESSAGE)));
    }
  }, [curAgentState, dispatch, messages.length, t]);

  useEffect(() => {
    if (autoMode && curAgentState === AgentState.AWAITING_USER_INPUT) {
      handleAutoMsg();
    }
  }, [autoMode, curAgentState]);

  useEffect(() => {
    if (
      (!autoMode && curAgentState === AgentState.AWAITING_USER_INPUT) ||
      curAgentState === AgentState.ERROR ||
      curAgentState === AgentState.INIT
    ) {
      if (document.cookie.indexOf("audio") !== -1) beep();
    }
  }, [curAgentState]);

  return (
    <div className="flex flex-col h-full bg-neutral-800">
      <div className="flex items-center gap-2 border-b border-neutral-600 text-sm px-4 py-2">
        <IoMdChatbubbles />
        Chat
        <div className="ml-auto">
          <Tooltip content="⚠️ Use with caution! The agent will automatically continue task execution without requesting user inputs.">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={autoMode}
                onChange={() => setAutoMode(!autoMode)}
                aria-label="Auto Mode"
              />
              <span>Auto Mode</span>
            </label>
          </Tooltip>
        </div>
      </div>
      <div className="flex-1 flex flex-col relative min-h-0">
        <div
          ref={scrollRef}
          className="overflow-y-auto p-3"
          onScroll={(e) => onChatBodyScroll(e.currentTarget)}
        >
          <Chat messages={messages} curAgentState={curAgentState} />
        </div>
      </div>

      <div className="relative">
        <div className="absolute bottom-2 left-0 right-0 flex items-center justify-center">
          {!hitBottom && (
            <ScrollButton
              onClick={scrollDomToBottom}
              icon={<VscArrowDown className="inline mr-2 w-3 h-3" />}
              label={t(I18nKey.CHAT_INTERFACE$TO_BOTTOM)}
            />
          )}
          {hitBottom && (
            <>
              {curAgentState === AgentState.AWAITING_USER_INPUT &&
                !autoMode && (
                  <ScrollButton
                    onClick={handleSendContinueMsg}
                    icon={
                      <RiArrowRightDoubleLine className="inline mr-2 w-3 h-3" />
                    }
                    label={t(I18nKey.CHAT_INTERFACE$INPUT_CONTINUE_MESSAGE)}
                  />
                )}
              {curAgentState === AgentState.RUNNING && <TypingIndicator />}
            </>
          )}
        </div>

        {feedbackShared !== messages.length && messages.length > 3 && (
          <div className="flex justify-start gap-2 p-2">
            <ScrollButton
              onClick={() => shareFeedback("positive")}
              icon={<FaRegThumbsUp className="inline mr-2 w-3 h-3" />}
              label=""
            />
            <ScrollButton
              onClick={() => shareFeedback("negative")}
              icon={<FaRegThumbsDown className="inline mr-2 w-3 h-3" />}
              label=""
            />
          </div>
        )}
      </div>

      <ChatInput
        disabled={
          curAgentState === AgentState.LOADING ||
          curAgentState === AgentState.AWAITING_USER_CONFIRMATION
        }
        onSendMessage={handleSendMessage}
      />
      <FeedbackModal
        polarity={feedbackPolarity}
        isOpen={feedbackModalIsOpen}
        onOpenChange={onFeedbackModalOpenChange}
        onSendFeedback={() => setFeedbackShared(messages.length)}
      />
    </div>
  );
}

export default ChatInterface;
