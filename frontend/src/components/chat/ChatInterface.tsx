import React, { useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RiArrowRightDoubleLine } from "react-icons/ri";
import { useTranslation } from "react-i18next";
import { VscArrowDown } from "react-icons/vsc";
import { useFetcher } from "@remix-run/react";
import Chat from "./Chat";
import TypingIndicator from "./TypingIndicator";
import { RootState } from "#/store";
import AgentState from "#/types/AgentState";
import { createChatMessage } from "#/services/chatService";
import { addUserMessage, addAssistantMessage } from "#/state/chatSlice";
import { I18nKey } from "#/i18n/declaration";
import { useScrollToBottom } from "#/hooks/useScrollToBottom";
import { useSocket } from "#/context/socket";
import { cn, removeApiKey, removeUnwantedKeys } from "#/utils/utils";
import { InteractiveChatBox } from "../interactive-chat-box";
import { convertImageToBase64 } from "#/utils/convert-image-to-base-64";
import { generateAgentStateChangeEvent } from "#/services/agentStateService";
import { FeedbackActions } from "../feedback-actions";
import { Feedback } from "#/api/open-hands.types";
import { getToken } from "#/services/auth";
import { clientAction } from "#/routes/submit-feedback";
import { FeedbackModal } from "../feedback-modal";
import { ScrollButton } from "../scroll-button";

const FEEDBACK_VERSION = "1.0";

export function ChatInterface() {
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const { send, events } = useSocket();
  const { messages } = useSelector((state: RootState) => state.chat);
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const fetcher = useFetcher<typeof clientAction>({ key: "feedback" });

  const [feedbackPolarity, setFeedbackPolarity] = React.useState<
    "positive" | "negative"
  >("positive");
  const [feedbackShared, setFeedbackShared] = React.useState(0);
  const [feedbackModalIsOpen, setFeedbackModalIsOpen] = React.useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const { scrollDomToBottom, onChatBodyScroll, hitBottom } =
    useScrollToBottom(scrollRef);

  const handleSendMessage = async (content: string, files: File[]) => {
    const promises = files.map((file) => convertImageToBase64(file));
    const imageUrls = await Promise.all(promises);

    const timestamp = new Date().toISOString();
    dispatch(addUserMessage({ content, imageUrls, timestamp }));
    send(createChatMessage(content, imageUrls, timestamp));
  };

  const handleStop = () => {
    send(generateAgentStateChangeEvent(AgentState.STOPPED));
  };

  const onClickShareFeedbackActionButton = async (
    polarity: "positive" | "negative",
  ) => {
    setFeedbackModalIsOpen(true);
    setFeedbackPolarity(polarity);
  };

  const handleSendContinueMsg = () => {
    handleSendMessage(t(I18nKey.CHAT_INTERFACE$INPUT_CONTINUE_MESSAGE), []);
  };

  React.useEffect(() => {
    if (curAgentState === AgentState.INIT && messages.length === 0) {
      dispatch(addAssistantMessage(t(I18nKey.CHAT_INTERFACE$INITIAL_MESSAGE)));
    }
  }, [curAgentState, dispatch, messages.length, t]);

  const handleSubmitFeedback = (
    permissions: "private" | "public",
    email: string,
  ) => {
    const feedback: Feedback = {
      version: FEEDBACK_VERSION,
      feedback: feedbackPolarity,
      email,
      permissions,
      token: getToken(),
      trajectory: removeApiKey(removeUnwantedKeys(events)),
    };

    const formData = new FormData();
    formData.append("feedback", JSON.stringify(feedback));

    fetcher.submit(formData, {
      action: "/submit-feedback",
      method: "POST",
    });

    setFeedbackShared(messages.length);
  };

  return (
    <div className="flex flex-col h-full justify-between">
      <div
        ref={scrollRef}
        onScroll={(e) => onChatBodyScroll(e.currentTarget)}
        className="flex flex-col max-h-full overflow-y-auto"
      >
        <Chat messages={messages} curAgentState={curAgentState} />
      </div>

      <div className="px-4 pb-4">
        {feedbackShared !== messages.length && messages.length > 3 && (
          <FeedbackActions
            onPositiveFeedback={() =>
              onClickShareFeedbackActionButton("positive")
            }
            onNegativeFeedback={() =>
              onClickShareFeedbackActionButton("negative")
            }
          />
        )}
        <div className="relative">
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

        <InteractiveChatBox
          isDisabled={
            curAgentState === AgentState.LOADING ||
            curAgentState === AgentState.AWAITING_USER_CONFIRMATION
          }
          mode={curAgentState === AgentState.RUNNING ? "stop" : "submit"}
          onSubmit={handleSendMessage}
          onStop={handleStop}
        />
      </div>
      <FeedbackModal
        isOpen={feedbackModalIsOpen}
        isSubmitting={fetcher.state === "submitting"}
        onClose={() => setFeedbackModalIsOpen(false)}
        onSubmit={handleSubmitFeedback}
      />
    </div>
  );
}
