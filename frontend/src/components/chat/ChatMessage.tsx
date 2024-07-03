import React, { useState } from "react";
import Markdown from "react-markdown";
import { useSelector } from "react-redux";
import store, { RootState } from "#/store";
import AgentState from "#/types/AgentState";
import { FaClipboard, FaClipboardCheck } from "react-icons/fa";
import { twMerge } from "tailwind-merge";
import { useTranslation } from "react-i18next";
import { code } from "../markdown/code";
import toast from "#/utils/toast";
import { I18nKey } from "#/i18n/declaration";
import { getSettings } from "#/services/settings";
import ConfirmIcon from "#/assets/confirm";
import RejectIcon from "#/assets/reject";
import { changeAgentState } from "#/services/agentStateService";
import { Tooltip } from "@nextui-org/react";

interface MessageProps {
  message: Message;
  isLastMessage: boolean;
}

function ChatMessage({ message, isLastMessage }: MessageProps) {
  const [isCopy, setIsCopy] = useState(false);
  const [isHovering, setIsHovering] = useState(false);

  const { CONFIRMATION_MODE } = getSettings();
  let curAgentState;
  if (CONFIRMATION_MODE) {
    curAgentState = useSelector((state: RootState) => state.agent).curAgentState;
  }

  const className = twMerge(
    "markdown-body",
    "p-3 text-white max-w-[90%] overflow-y-auto rounded-lg relative",
    message.sender === "user" ? "bg-neutral-700 self-end" : "bg-neutral-500",
  );

  const { t } = useTranslation();
  const copyToClipboard = () => {
    navigator.clipboard
      .writeText(message.content)
      .then(() => {
        setIsCopy(true);
        setTimeout(() => {
          setIsCopy(false);
        }, 1500);
        toast.info(t(I18nKey.CHAT_INTERFACE$CHAT_MESSAGE_COPIED));
      })
      .catch(() => {
        toast.error(
          "copy-error",
          t(I18nKey.CHAT_INTERFACE$CHAT_MESSAGE_COPY_FAILED),
        );
      });
  };

  return (
    <div
      data-testid="message"
      className={className}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      {isHovering && (
        <button
          onClick={copyToClipboard}
          className="absolute top-1 right-1 p-1 bg-neutral-600 rounded hover:bg-neutral-700"
          aria-label={t(I18nKey.CHAT_INTERFACE$TOOLTIP_COPY_MESSAGE)}
          type="button"
        >
          {isCopy ? <FaClipboardCheck /> : <FaClipboard />}
        </button>
      )}
      <Markdown components={{ code }}>{message.content}</Markdown>
      {isLastMessage && CONFIRMATION_MODE && curAgentState === AgentState.AWAITING_USER_CONFIRMATION && (
        <div className="flex justify-between items-center pt-4">
        <p>Do you want to continue with this action?</p>
        <div className="flex items-center gap-3">
          <Tooltip content="Confirm the requested action" closeDelay={100}>
            <button className="bg-neutral-700 rounded-full p-1 hover:bg-neutral-800" onClick={()=>{changeAgentState(AgentState.ACTION_CONFIRMED)}}>
              <ConfirmIcon />
            </button>
          </Tooltip>
          <Tooltip content="Reject the requested action" closeDelay={100}>
            <button className="bg-neutral-700 rounded-full p-1 hover:bg-neutral-800" onClick={()=>{changeAgentState(AgentState.ACTION_REJECTED)}}>
              <RejectIcon />
            </button>
          </Tooltip>
      </div>
      </div>
      )}
    </div>
  );
}

export default ChatMessage;
