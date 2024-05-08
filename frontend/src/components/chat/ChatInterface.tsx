import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { IoMdChatbubbles } from "react-icons/io";
import ChatInput from "./ChatInput";
import Chat from "./Chat";
import { RootState } from "#/store";
import AgentState from "#/types/AgentState";
import { sendChatMessage } from "#/services/chatService";
import { addUserMessage } from "#/state/chatSlice";

function ChatInterface() {
  const dispatch = useDispatch();
  const { messages } = useSelector((state: RootState) => state.chat);
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const handleSendMessage = (content: string) => {
    dispatch(addUserMessage(content));
    sendChatMessage(content);
  };

  return (
    <div className="flex flex-col h-full bg-neutral-800">
      <div className="flex items-center gap-2 border-b border-neutral-600 text-sm px-4 py-2">
        <IoMdChatbubbles />
        Chat
      </div>
      <div className="flex-1 flex flex-col relative min-h-0">
        <div className="overflow-x-auto p-3">
          <Chat messages={messages} />
        </div>
        {/* Fade between messages and input */}
        <div className="absolute bottom-0 left-0 right-0 h-4 bg-gradient-to-b from-transparent to-neutral-800" />
      </div>
      <ChatInput
        disabled={curAgentState === AgentState.LOADING}
        onSendMessage={handleSendMessage}
      />
    </div>
  );
}

export default ChatInterface;
