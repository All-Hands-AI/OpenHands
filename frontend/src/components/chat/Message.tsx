import React from "react";
import Markdown from "react-markdown";

type Message = {
  sender: "user" | "assistant";
  content: string;
};

interface MessageProps {
  message: Message;
}

function ChatMessage({ message }: MessageProps) {
  return (
    <div
      data-testid="chat-bubble"
      className={message.sender === "user" ? "self-end" : ""}
    >
      <Markdown>{message.content}</Markdown>
    </div>
  );
}

export default ChatMessage;
