import { Card, CardBody } from "@nextui-org/react";
import React, { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import assistantAvatar from "../assets/assistant-avatar.png";
import userAvatar from "../assets/user-avatar.png";
import { useTypingEffect } from "../hooks/useTypingEffect";
import { I18nKey } from "../i18n/declaration";
import {
  addAssistantMessageToChat,
  setCurrentQueueMarkerState,
  setCurrentTypingMsgState,
  setTypingAcitve,
} from "../services/chatService";
import { Message } from "../state/chatSlice";
import { RootState } from "../store";
import Input from "./Input";

interface IChatBubbleProps {
  msg: Message;
}

/**
 * @returns jsx
 *
 * component used for typing effect when assistant replies
 *
 * makes uses of useTypingEffect hook
 *
 */
function TypingChat() {
  const { currentTypingMessage, currentQueueMarker, queuedTyping, messages } =
    useSelector((state: RootState) => state.chat);

  const messageContent = useTypingEffect([currentTypingMessage], {
    loop: false,
    setTypingAcitve,
    setCurrentQueueMarkerState,
    currentQueueMarker,
    playbackRate: 0.1,
    addAssistantMessageToChat,
    assistantMessageObj: messages?.[queuedTyping[currentQueueMarker]],
  });

  return (
    currentQueueMarker !== null && (
      <Card className="bg-success-100">
        <CardBody>{messageContent}</CardBody>
      </Card>
    )
  );
}

function ChatBubble({ msg }: IChatBubbleProps): JSX.Element {
  return (
    <div className="flex mb-2.5 pr-5 pl-5">
      <div
        className={`flex mt-2.5 mb-0 min-w-0 ${msg?.sender === "user" && "flex-row-reverse ml-auto"}`}
      >
        <img
          src={msg?.sender === "user" ? userAvatar : assistantAvatar}
          alt={`${msg?.sender} avatar`}
          className="w-[40px] h-[40px] mx-2.5"
        />
        <Card className={`${msg?.sender === "user" ? "bg-primary-100" : ""}`}>
          <CardBody>{msg?.content}</CardBody>
        </Card>
      </div>
    </div>
  );
}

function MessageList(): JSX.Element {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const {
    messages,
    queuedTyping,
    typingActive,
    currentQueueMarker,
    currentTypingMessage,
    newChatSequence,
  } = useSelector((state: RootState) => state.chat);

  const messageScroll = () => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  };

  useEffect(() => {
    messageScroll();
    if (!typingActive) return;

    const interval = setInterval(() => {
      messageScroll();
    }, 1000);

    // eslint-disable-next-line consistent-return
    return () => clearInterval(interval);
  }, [newChatSequence, typingActive]);

  useEffect(() => {
    const newMessage = messages?.[queuedTyping[currentQueueMarker]]?.content;

    if (
      currentQueueMarker !== null &&
      currentQueueMarker !== 0 &&
      currentTypingMessage !== newMessage
    ) {
      setCurrentTypingMsgState(
        messages?.[queuedTyping?.[currentQueueMarker]]?.content,
      );
    }
  }, [queuedTyping]);

  useEffect(() => {
    if (currentTypingMessage === "") return;

    if (!typingActive) setTypingAcitve(true);
  }, [currentTypingMessage]);

  useEffect(() => {
    const newMessage = messages?.[queuedTyping[currentQueueMarker]]?.content;
    if (
      newMessage &&
      typingActive === false &&
      currentTypingMessage !== newMessage
    ) {
      if (currentQueueMarker !== 0) {
        setCurrentTypingMsgState(
          messages?.[queuedTyping?.[currentQueueMarker]]?.content,
        );
      }
    }
  }, [typingActive]);

  useEffect(() => {
    if (currentQueueMarker === 0) {
      setCurrentTypingMsgState(messages?.[queuedTyping?.[0]]?.content);
    }
  }, [currentQueueMarker]);

  return (
    <div className="flex-1 overflow-y-auto">
      {newChatSequence.map((msg, index) =>
        // eslint-disable-next-line no-nested-ternary
        msg.sender === "user" || msg.sender === "assistant" ? (
          <ChatBubble key={index} msg={msg} />
        ) : (
          <div key={index} />
        ),
      )}

      {typingActive && (
        <div className="flex mb-2.5 pr-5 pl-5 bg-s">
          <div className="flex mt-2.5 mb-0 min-w-0 ">
            <img
              src={assistantAvatar}
              alt="assistant avatar"
              className="w-[40px] h-[40px] mx-2.5"
            />
            <TypingChat />
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}

function InitializingStatus(): JSX.Element {
  const { t } = useTranslation();

  return (
    <div className="flex items-center m-auto h-full">
      <img
        src={assistantAvatar}
        alt="assistant avatar"
        className="w-[40px] h-[40px] mx-2.5"
      />
      <div>{t(I18nKey.CHAT_INTERFACE$INITIALZING_AGENT_LOADING_MESSAGE)}</div>
    </div>
  );
}

function ChatInterface(): JSX.Element {
  const { initialized } = useSelector((state: RootState) => state.task);

  return (
    <div className="flex flex-col h-full p-0 bg-bg-workspace">
      <div className="border-b border-border text-lg px-4 py-2">Chat</div>
      {initialized ? <MessageList /> : <InitializingStatus />}
      <Input />
    </div>
  );
}

export default ChatInterface;
