import React from "react";
import { useDispatch, useSelector } from "react-redux";
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
    <div>
      <Chat messages={messages} />
      <ChatInput onSendMessage={handleSendMessage} />
    </div>
  );
}

export default ChatInterface;
