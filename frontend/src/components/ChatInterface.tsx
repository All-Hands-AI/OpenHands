import React from "react";
import { useSelector } from "react-redux";
import CogTooth from "../assets/cog-tooth";
import { RootState } from "../store";
import Input from "./chatUIComponents/Input";
import InitializingStatus from "./chatUIComponents/InitializingStatus";
import { IChatInterfaceProps } from "../types/chatUI/TypesChatInterface";
import MessageList from "./chatUIComponents/MessageList";

function ChatInterface({ setSettingOpen }: IChatInterfaceProps): JSX.Element {
  const { initialized } = useSelector((state: RootState) => state.task);
  return (
    <div className="flex flex-col h-full p-0 bg-bg-light">
      <div className="w-full flex justify-between p-5">
        <div />
        <div
          className="cursor-pointer hover:opacity-80"
          onClick={() => setSettingOpen(true)}
        >
          <CogTooth />
        </div>
      </div>
      {initialized ? <MessageList /> : <InitializingStatus />}
      <Input />
    </div>
  );
}

export default ChatInterface;
