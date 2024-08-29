import React from "react";
import ChatMessage from "./ChatMessage";
import { SimplifiedMessage } from "#/utils/extractMessage";

interface ChatProps {
  messages: SimplifiedMessage[];
  curAgentState: AgentState;
}

function Chat({ messages, curAgentState }: ChatProps) {
  return (
    <div className="flex flex-col gap-3">
      {messages.map((message, index) => (
        <ChatMessage
          key={index}
          message={message}
          isLastMessage={messages && index === messages.length - 1}
          awaitingUserConfirmation={
            curAgentState === "awaiting_user_confirmation"
          }
        />
      ))}
    </div>
  );
}

export default Chat;
