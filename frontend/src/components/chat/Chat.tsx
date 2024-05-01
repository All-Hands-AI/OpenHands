import React from "react";
import ChatMessage from "./ChatMessage";

interface ChatProps {
  messages: Message[];
}

function Chat({ messages }: ChatProps) {
  return (
    <div>
      {messages.map((message, index) => (
        <ChatMessage key={index} message={message} />
      ))}
    </div>
  );
}

export default Chat;
