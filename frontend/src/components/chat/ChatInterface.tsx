import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { IoMdChatbubbles } from "react-icons/io";
import ChatInput from "../ChatInput";
import Chat from "./Chat";
import { RootState } from "#/store";
import AgentTaskState from "#/types/AgentTaskState";
import { addUserMessage } from "#/state/chatSlice";
import ActionType from "#/types/ActionType";
import Socket from "#/services/socket";

function ActionBanner() {
  return (
    <div
      data-testid="typing"
      className="flex items-center justify-center gap-2 bg-neutral-700 border-y border-neutral-500 py-1.5 px-4"
    >
      <div className="flex h-5 w-5 items-center justify-center" />
      <p className="text-sm text-gray-200 dark:text-gray-200">Working...</p>
    </div>
  );
}

function ChatInterface() {
  const { messages } = useSelector((state: RootState) => state.chat);
  const { curTaskState } = useSelector((state: RootState) => state.agent);

  const dispatch = useDispatch();

  const handleSendMessage = (content: string) => {
    dispatch(addUserMessage(content));

    let event;
    if (curTaskState === AgentTaskState.INIT) {
      event = { action: ActionType.START, args: { task: content } };
    } else {
      event = { action: ActionType.USER_MESSAGE, args: { content } };
    }

    Socket.send(JSON.stringify(event));
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
        {curTaskState === AgentTaskState.RUNNING && <ActionBanner />}
        {/* Fade between messages and input */}
        <div className="absolute bottom-0 left-0 right-0 h-4 bg-gradient-to-b from-transparent to-neutral-800" />
      </div>
      <ChatInput onSendMessage={handleSendMessage} />
    </div>
  );
}

export default ChatInterface;
