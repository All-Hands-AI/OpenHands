import React, { useEffect, useRef, useState } from "react";
import { useSelector } from "react-redux";
import { Card, CardBody } from "@nextui-org/react";
import assistantAvatar from "../assets/assistant-avatar.png";
import userAvatar from "../assets/user-avatar.png";
import { sendChatMessage } from "../services/chatService";
import { RootState } from "../store";
import CogTooth from "../assets/cog-tooth";

function MessageList(): JSX.Element {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages } = useSelector((state: RootState) => state.chat);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto">
      {messages.map((msg, index) => (
        <div key={index} className="flex mb-2.5">
          <div
            className={`${msg.sender === "user" ? "flex flex-row-reverse mt-2.5 mr-2.5 mb-0 ml-auto" : "flex"}`}
          >
            <img
              src={msg.sender === "user" ? userAvatar : assistantAvatar}
              alt={`${msg.sender} avatar`}
              className="w-[40px] h-[40px] mx-2.5"
            />
            <Card className="w-4/5">
              <CardBody>{msg.content}</CardBody>
            </Card>
          </div>
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
}

function InitializingStatus(): JSX.Element {
  return (
    <div className="flex items-center m-auto h-full">
      <img
        src={assistantAvatar}
        alt="assistant avatar"
        className="w-[40px] h-[40px] mx-2.5"
      />
      <div>Initializing agent (may take up to 10 seconds)...</div>
    </div>
  );
}

interface Props {
  setSettingOpen: (isOpen: boolean) => void;
}

function ChatInterface({ setSettingOpen }: Props): JSX.Element {
  const { initialized } = useSelector((state: RootState) => state.task);
  const [inputMessage, setInputMessage] = useState("");

  const handleSendMessage = () => {
    if (inputMessage.trim() !== "") {
      sendChatMessage(inputMessage);
      setInputMessage("");
    }
  };

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
      <div className="w-full flex items-center p-5 rounded-none rounded-bl-lg rounded-br-lg">
        <div className="w-full flex items-center rounded-xl text-base bg-bg-input">
          <input
            type="text"
            className="flex-1 py-4 px-2.5 border-none mx-4 bg-bg-input text-white outline-none"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Send a message (won't interrupt the Assistant)"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSendMessage();
              }
            }}
          />
          <button
            type="button"
            className="bg-transparent border-none rounded py-2.5 px-5 hover:opacity-80 cursor-pointer select-none"
            onClick={handleSendMessage}
            disabled={!initialized}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;
