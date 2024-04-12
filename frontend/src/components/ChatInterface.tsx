import { Card, CardBody } from "@nextui-org/react";
import React, { useEffect, useRef } from "react";
import { useSelector } from "react-redux";
import { useTypingEffect } from "../hooks/useTypingEffect";
import {
  addAssistantMessageToChat,
  setTypingActive,
  takeOneAndType,
} from "../services/chatService";
import { Message } from "../state/chatSlice";
import { RootState } from "../store";
import AgentStatusBar from "./AgentStatusBar";
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
    <Card className="bg-neutral-500">
      <CardBody>{messageContent}</CardBody>
    </Card>
  );
}

function ChatBubble({ msg }: IChatBubbleProps): JSX.Element {
  return (
    <div
      className={`flex mb-2.5 pr-5 pl-5 max-w-[90%] ${msg?.sender === "user" ? "self-end" : ""}`}
    >
      <div
        className={`flex mt-2.5 mb-0 min-w-0 ${msg?.sender === "user" && "flex-row-reverse ml-auto"}`}
      >
        <Card
          className={`${msg?.sender === "user" ? "bg-neutral-700" : "bg-neutral-500"}`}
        >
          <CardBody>{msg?.content}</CardBody>
        </Card>
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
    <div className="flex-1 overflow-y-auto flex flex-col">
      {newChatSequence.map((msg, index) => (
        <ChatBubble key={index} msg={msg} />
      ))}

      {typingActive && (
        <div className="flex mb-2.5 pr-5 pl-5 bg-s">
          <div className="flex mt-2.5 mb-0 min-w-0 ">
            <TypingChat />
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}

function ChatInterface(): JSX.Element {
  const { initialized } = useSelector((state: RootState) => state.task);

  return (
    <div className="flex flex-col h-full p-0 bg-neutral-800">
      <div className="border-b border-neutral-600 text-sm px-4 py-2">Chat</div>
      <MessageList />
      {initialized ? null : <AgentStatusBar />}
      <Input />
    </div>
  );
}

export default ChatInterface;
