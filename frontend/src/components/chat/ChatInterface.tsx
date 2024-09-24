import React, { useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RiArrowRightDoubleLine } from "react-icons/ri";
import { useTranslation } from "react-i18next";
import { VscArrowDown } from "react-icons/vsc";
import { useDisclosure } from "@nextui-org/react";
import ChatInput from "./ChatInput";
import Chat from "./Chat";
import TypingIndicator from "./TypingIndicator";
import { RootState } from "#/store";
import AgentState from "#/types/AgentState";
import { createChatMessage } from "#/services/chatService";
import { addUserMessage, addAssistantMessage } from "#/state/chatSlice";
import { I18nKey } from "#/i18n/declaration";
import { useScrollToBottom } from "#/hooks/useScrollToBottom";
import FeedbackModal from "../modals/feedback/FeedbackModal";
import { useSocket } from "#/context/socket";
import ThumbsUpIcon from "#/assets/thumbs-up.svg?react";
import ThumbsDownIcon from "#/assets/thumbs-down.svg?react";
import { cn } from "#/utils/utils";

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
  const { send } = useSocket();
  const { messages } = useSelector((state: RootState) => state.chat);
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

  const handleSendMessage = (content: string, imageUrls: string[]) => {
    const timestamp = new Date().toISOString();
    dispatch(addUserMessage({ content, imageUrls, timestamp }));
    send(createChatMessage(content, imageUrls, timestamp));
  };

  const shareFeedback = async (polarity: "positive" | "negative") => {
    onFeedbackModalOpen();
    setFeedbackPolarity(polarity);
  };

  const { t } = useTranslation();
  const handleSendContinueMsg = () => {
    handleSendMessage(t(I18nKey.CHAT_INTERFACE$INPUT_CONTINUE_MESSAGE), []);
  };

  const scrollRef = useRef<HTMLDivElement>(null);

  const { scrollDomToBottom, onChatBodyScroll, hitBottom } =
    useScrollToBottom(scrollRef);

  React.useEffect(() => {
    if (curAgentState === AgentState.INIT && messages.length === 0) {
      dispatch(addAssistantMessage(t(I18nKey.CHAT_INTERFACE$INITIAL_MESSAGE)));
    }
  }, [curAgentState, dispatch, messages.length, t]);

  return (
    <div className="flex flex-col h-full justify-between">
      <div
        ref={scrollRef}
        onScroll={(e) => onChatBodyScroll(e.currentTarget)}
        className="flex flex-col max-h-full overflow-y-auto"
      >
        <Chat messages={messages} curAgentState={curAgentState} />
      </div>

      <div>
        <div className="relative">
          {feedbackShared !== messages.length && messages.length > 3 && (
            <div
              className={cn(
                "flex justify-start gap-[7px]",
                "absolute left-3 bottom-[6.5px]",
              )}
            >
              <button
                type="button"
                onClick={() => shareFeedback("positive")}
                className="p-1 bg-neutral-700 border border-neutral-600 rounded"
              >
                <ThumbsUpIcon width={15} height={15} />
              </button>
              <button
                type="button"
                onClick={() => shareFeedback("negative")}
                className="p-1 bg-neutral-700 border border-neutral-600 rounded"
              >
                <ThumbsDownIcon width={15} height={15} />
              </button>
            </div>
          )}

          <div className="absolute left-1/2 transform -translate-x-1/2 bottom-[6.5px]">
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
                  <button
                    type="button"
                    onClick={handleSendContinueMsg}
                    className={cn(
                      "px-2 py-1 bg-neutral-700 border border-neutral-600 rounded",
                      "text-[11px] leading-4 tracking-[0.01em] font-[500]",
                      "flex items-center gap-2",
                    )}
                  >
                    <RiArrowRightDoubleLine className="w-3 h-3" />
                    {t(I18nKey.CHAT_INTERFACE$INPUT_CONTINUE_MESSAGE)}
                  </button>
                )}
                {curAgentState === AgentState.RUNNING && <TypingIndicator />}
              </>
            )}
          </div>
        </div>

        <ChatInput
          disabled={
            curAgentState === AgentState.LOADING ||
            curAgentState === AgentState.AWAITING_USER_CONFIRMATION
          }
          onSendMessage={handleSendMessage}
        />
      </div>
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
