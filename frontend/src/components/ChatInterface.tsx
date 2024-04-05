import React, { useEffect, useRef } from "react";
import { useSelector } from "react-redux";
import { RootState } from "../store";
import MessageList from "./chatUIComponents/MessageList";
import InitializingStatus from "./chatUIComponents/InitializingStatus";
import Input from "./chatUIComponents/Input";

function ChatInterface(): JSX.Element {
  const { initialized } = useSelector((state: RootState) => state.task);

  return (
    <div className="flex flex-col h-full p-0 bg-bg-workspace">
      <div className="border-b border-border text-lg px-4 py-2">Chat</div>
      {initialized ? <MessageList /> : <InitializingStatus />}
      <Input />
    </div>
  );
}

export default ChatInterface;
