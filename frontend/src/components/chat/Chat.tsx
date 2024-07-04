import React from "react";
import { useSelector } from "react-redux";
import ChatMessage from "./ChatMessage";
import { RootState } from "#/store";
import AgentState from "#/types/AgentState";

interface ChatProps {
  messages: Message[];
}

function Chat({ messages }: ChatProps) {
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  return (
    <div className="flex flex-col gap-3">
      {messages.map((message, index) => (
        <ChatMessage
          key={index}
          message={message}
          isLastMessage={messages && index === messages.length - 1}
          awaitsUserConfirmation={
            curAgentState === AgentState.AWAITING_USER_CONFIRMATION
          }
        />
      ))}
    </div>
  );
}

export default Chat;
