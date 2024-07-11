// frontend/src/components/chat/ChatInterface.tsx
import React, { useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
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
import { sendChatMessage } from "#/services/chatService";
import { addUserMessage, addAssistantMessage } from "#/state/chatSlice";
import { I18nKey } from "#/i18n/declaration";
import { useScrollToBottom } from "#/hooks/useScrollToBottom";
import { Feedback } from "#/services/feedbackService";
import FeedbackModal from "../modals/feedback/FeedbackModal";
import { removeApiKey } from "#/utils/utils";
import Session from "#/services/session";
import { getToken } from "#/services/auth";

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

  const feedbackVersion = "1.0";
  const [feedback, setFeedback] = React.useState<Feedback>({
    email: "",
    feedback: "positive",
    permissions: "private",
    trajectory: [],
    token: "",
    version: feedbackVersion,
  });
  const [feedbackShared, setFeedbackShared] = React.useState(0);

  const {
    isOpen: feedbackModalIsOpen,
    onOpen: onFeedbackModalOpen,
    onOpenChange: onFeedbackModalOpenChange,
  } = useDisclosure();

  const shareFeedback = async (polarity: "positive" | "negative") => {
    setFeedback((prev) => ({
      ...prev,
      feedback: polarity,
      trajectory: removeApiKey(Session._history),
      token: getToken(),
    }));
    onFeedbackModalOpen();
  };

  const handleSendMessage = (content: string) => {
    dispatch(addUserMessage(content));
    sendChatMessage(content);
  };

  const handleEmailChange = (key: string) => {
    setFeedback({ ...feedback, email: key } as Feedback);
  };

  const handlePermissionsChange = (permissions: "public" | "private") => {
    setFeedback({ ...feedback, permissions } as Feedback);
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
  }, [curAgentState, dispatch, messages.length, t]);

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
        disabled={curAgentState === AgentState.LOADING}
        onSendMessage={handleSendMessage}
      />
      <FeedbackModal
        feedback={feedback}
        handleEmailChange={handleEmailChange}
        handlePermissionsChange={handlePermissionsChange}
        isOpen={feedbackModalIsOpen}
        onOpenChange={onFeedbackModalOpenChange}
        onSendFeedback={() => setFeedbackShared(messages.length)}
      />
    </div>
  );
}

export default ChatInterface;
