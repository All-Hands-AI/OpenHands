import React, { useEffect, useRef } from "react";
import { useSelector } from "react-redux";
import assistantAvatar from "../../assets/assistant-avatar.png";
import { RootState } from "../../store";
import {
  setCurrentTypingMsgState,
  setTypingAcitve,
} from "../../services/chatService";
import ChatBubble from "./ChatBubble";
import TypingChat from "./TypingChat";

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

export default MessageList;
