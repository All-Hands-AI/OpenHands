import React from "react";
import ChatMessage from "./ChatMessage";
import AgentState from "#/types/AgentState";

interface ChatProps {
  messages: Message[];
  curAgentState?: AgentState;
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
            curAgentState === AgentState.AWAITING_USER_CONFIRMATION
          }
        />
      ))}
    </div>
  );
}

export default Chat;
