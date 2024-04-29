import React from "react";

type Message = {
  sender: "user" | "assistant";
  content: string;
};

interface MessageProps {
  message: Message;
}

function ChatMessage({ message }: MessageProps) {
  return (
    <div className={message.sender === "user" ? "self-end" : ""}>
      {message.content}
    </div>
  );
}

export default ChatMessage;
