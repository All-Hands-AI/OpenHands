import React, { useEffect, useRef } from "react";
import { IoMdChatbubbles } from "react-icons/io";
import Markdown from "react-markdown";
import { useSelector } from "react-redux";
import { useTypingEffect } from "#/hooks/useTypingEffect";
import {
  addAssistantMessageToChat,
  sendChatMessage,
  setTypingActive,
  takeOneAndType,
} from "#/services/chatService";
import { Message } from "#/state/chatSlice";
import { RootState } from "#/store";
import ChatInput from "./ChatInput";

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
  const { typeThis } = useSelector((state: RootState) => state.chat);

  const messageContent = useTypingEffect([typeThis?.content], {
    loop: false,
    setTypingActive,
    playbackRate: 0.099,
    addAssistantMessageToChat,
    takeOneAndType,
    typeThis,
  });

  return (
    <div className="flex max-w-[90%]">
      <div className="flex mb-0 min-w-0">
        <div className="bg-neutral-500 rounded-lg">
          <div className="p-3">{messageContent}</div>
        </div>
      </div>
    </div>
  );
}

function ChatBubble({ msg }: IChatBubbleProps): JSX.Element {
  return (
    <div
      className={`flex max-w-[90%] ${msg?.sender === "user" ? "self-end" : ""}`}
    >
      <div
        className={`flex mb-0 min-w-0 ${msg?.sender === "user" && "flex-row-reverse ml-auto"}`}
      >
        <div
          className={`${msg?.sender === "user" ? "bg-neutral-700" : "bg-neutral-500"} rounded-lg`}
        >
          <div className="p-3 prose prose-invert text-white">
            <Markdown>{msg?.content}</Markdown>
          </div>
        </div>
      </div>
    </div>
  );
}

function MessageList(): JSX.Element {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { typingActive, newChatSequence, typeThis } = useSelector(
    (state: RootState) => state.chat,
  );

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
    if (typeThis.content === "") return;

    if (!typingActive) setTypingActive(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [typeThis]);

  return (
    <div className="flex-1 flex flex-col gap-3 pt-3 px-3 relative min-h-0">
      <div className="overflow-y-auto flex flex-col h-full gap-3">
        {newChatSequence.map((msg, index) => (
          <ChatBubble key={index} msg={msg} />
        ))}
        {typingActive && <TypingChat />}
        <div ref={messagesEndRef} />
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-4 bg-gradient-to-b from-transparent to-neutral-800" />
    </div>
  );
}

function ChatInterface(): JSX.Element {
  const { initialized } = useSelector((state: RootState) => state.task);

  return (
    <div className="flex flex-col h-full p-0 bg-neutral-800">
      <div className="flex items-center gap-2 border-b border-neutral-600 text-sm px-4 py-2">
        <IoMdChatbubbles />
        Chat
      </div>
      <MessageList />
      <ChatInput disabled={!initialized} onSendMessage={sendChatMessage} />
    </div>
  );
}

export default ChatInterface;
