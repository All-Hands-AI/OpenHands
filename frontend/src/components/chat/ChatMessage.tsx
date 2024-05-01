import React from "react";
import Markdown from "react-markdown";

interface MessageProps {
  message: Message;
}

function ChatMessage({ message }: MessageProps) {
  return (
    <div
      data-testid="message"
      className={message.sender === "user" ? "self-end" : ""}
    >
      <Markdown>{message.content}</Markdown>
    </div>
  );
}

export default ChatMessage;
