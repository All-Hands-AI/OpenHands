import React, { useRef } from "react";
import { useSelector } from "react-redux";
import { IoMdChatbubbles } from "react-icons/io";
import { RiArrowRightDoubleLine } from "react-icons/ri";
import { useTranslation } from "react-i18next";
import { VscArrowDown } from "react-icons/vsc";
import { FaRegThumbsDown, FaRegThumbsUp } from "react-icons/fa";
import { useDisclosure } from "@nextui-org/react";
import ChatInput from "./ChatInput";
import Chat from "./Chat";
import TypingIndicator from "./TypingIndicator";
import { RootState } from "#/store";
import AgentState from "#/types/AgentState";
import { I18nKey } from "#/i18n/declaration";
import { useScrollToBottom } from "#/hooks/useScrollToBottom";
import FeedbackModal from "../modals/feedback/FeedbackModal";
import { useSession } from "#/context/session";
import {
  SimplifiedMessage,
  simplifyMessage,
} from "#/utils/simplifyEventMessage";

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
  const { t } = useTranslation();
  const scrollRef = useRef<HTMLDivElement>(null);
  const { scrollDomToBottom, onChatBodyScroll, hitBottom } =
    useScrollToBottom(scrollRef);

  const { sendUserMessage, eventLog } = useSession();
  const [messages, setMessages] = React.useState<SimplifiedMessage[]>([]);
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const [feedbackPolarity, setFeedbackPolarity] = React.useState<
    "positive" | "negative"
  >("positive");
  const [feedbackShared, setFeedbackShared] = React.useState(0);

  const {
    isOpen: feedbackModalIsOpen,
    onOpen: onFeedbackModalOpen,
    onOpenChange: onFeedbackModalOpenChange,
  } = useDisclosure();

  React.useEffect(() => {
    const simplifiedMessages = eventLog
      .map((msg) => JSON.parse(msg))
      .map(simplifyMessage)
      .filter((msg): msg is SimplifiedMessage => msg !== null);
    setMessages(simplifiedMessages);
  }, [eventLog]);

  const shareFeedback = async (polarity: "positive" | "negative") => {
    onFeedbackModalOpen();
    setFeedbackPolarity(polarity);
  };

  const handleSendMessage = (content: string, imageUrls: string[]) => {
    sendUserMessage(content, imageUrls);
  };

  const handleSendContinueMsg = () => {
    handleSendMessage(t(I18nKey.CHAT_INTERFACE$INPUT_CONTINUE_MESSAGE), []);
  };

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
              {curAgentState === AgentState.AWAITING_USER_INPUT && (
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
