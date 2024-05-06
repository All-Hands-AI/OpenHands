import React from "react";
import ChatMessage from "./ChatMessage";

interface ChatProps {
  messages: Message[];
}

function Chat({ messages }: ChatProps) {
  const endOfMessagesRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col gap-3">
      {messages.map((message, index) => (
        <ChatMessage key={index} message={message} />
      ))}
      <div ref={endOfMessagesRef} />
    </div>
  );
}

export default Chat;
