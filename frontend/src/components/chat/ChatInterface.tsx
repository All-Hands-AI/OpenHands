import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { IoMdChatbubbles } from "react-icons/io";
import ChatInput from "../ChatInput";
import Chat from "./Chat";
import { RootState } from "#/store";
import { addUserMessage } from "#/state/chat";
import ActionType from "#/types/ActionType";
import Socket from "#/services/socket";

function ChatInterface() {
  const { messages } = useSelector((state: RootState) => state.tempChat);
  const dispatch = useDispatch();

  const handleSendMessage = (content: string) => {
    dispatch(addUserMessage(content));
    const event = { action: ActionType.START, args: { task: content } };

    Socket.send(JSON.stringify(event));
  };

  return (
    <div className="flex flex-col h-full bg-neutral-800">
      <div className="flex items-center gap-2 border-b border-neutral-600 text-sm px-4 py-2">
        <IoMdChatbubbles />
        Chat
      </div>
      <div className="flex flex-1 flex-col overflow-x-auto p-3">
        <Chat messages={messages} />
      </div>
      <ChatInput onSendMessage={handleSendMessage} />
    </div>
  );
}

export default ChatInterface;
