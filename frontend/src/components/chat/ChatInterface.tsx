import React from "react";
import ChatInput from "../ChatInput";
import Chat from "./Chat";

function ChatInterface() {
  const [messages, setMessages] = React.useState<Message[]>([]);

  const handleSendMessage = (content: string) => {
    const message: Message = { sender: "user", content };
    setMessages((prev) => [...prev, message]);
  };

  return (
    <div>
      <Chat messages={messages} />
      <ChatInput onSendMessage={handleSendMessage} />
    </div>
  );
}

export default ChatInterface;
