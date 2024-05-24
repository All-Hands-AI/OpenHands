import React, { useRef } from "react";
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
import Session from "#/services/session";
import { getToken } from "#/services/auth";
import toast from "#/utils/toast";
import { FeedbackData, sendFeedback } from "#/api";
import { removeApiKey } from "#/utils/utils";

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

  const [feedbackShared, setFeedbackShared] = React.useState(false);
  const [feedbackLoading, setFeedbackLoading] = React.useState(false);

  const shareFeedback = async (feedback: "positive" | "negative") => {
    const data: FeedbackData = {
      email: "NOT_PROVIDED",
      token: getToken(),
      feedback,
      trajectory: removeApiKey(Session._history),
    };

    try {
      setFeedbackLoading(true);
      await sendFeedback(data);
      toast.info("Feedback shared successfully.");
    } catch (e) {
      console.error(e);
      toast.error("share-error", "Failed to share, see console for details.");
    } finally {
      setFeedbackShared(true);
      setFeedbackLoading(false);
    }
  };

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

  React.useEffect(() => {
    if (curAgentState === AgentState.INIT && messages.length === 0) {
      dispatch(addAssistantMessage(t(I18nKey.CHAT_INTERFACE$INITIAL_MESSAGE)));
    }
  }, [curAgentState]);

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

        {!feedbackShared && messages.length > 3 && (
          <div className="flex justify-start gap-2 p-2">
            <ScrollButton
              disabled={feedbackLoading}
              onClick={() => shareFeedback("positive")}
              icon={<FaRegThumbsUp className="inline mr-2 w-3 h-3" />}
              label=""
            />
            <ScrollButton
              disabled={feedbackLoading}
              onClick={() => shareFeedback("negative")}
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
    </div>
  );
}

export default ChatInterface;
