import { Card, CardBody, Textarea } from "@nextui-org/react";
import React, { useEffect, useRef, useState } from "react";
import { useSelector } from "react-redux";
import assistantAvatar from "../assets/assistant-avatar.png";
import CogTooth from "../assets/cog-tooth";
import userAvatar from "../assets/user-avatar.png";
import { useTypingEffect } from "../hooks/useTypingEffect";
import { sendChatMessage } from "../services/chatService";
import { Message } from "../state/chatSlice";
import { RootState } from "../store";
import Loader from "./Loader";

interface ITypingChatProps {
  msg: Message;
}

/**
 * @param msg
 * @returns jsx
 *
 * component used for typing effect when assistant replies
 *
 * makes uses of useTypingEffect hook
 *
 */
function TypingChat({ msg }: ITypingChatProps) {
  return (
    // eslint-disable-next-line react/jsx-no-useless-fragment
    <>
      {msg?.content && (
        <Card>
          <CardBody>
            {useTypingEffect([msg?.content], { loop: false })}
          </CardBody>
        </Card>
      )}
    </>
  );
}

function MessageList(): JSX.Element {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages } = useSelector((state: RootState) => state.chat);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto">
      {messages.map((msg, index) => (
        <div key={index} className="flex mb-2.5 pr-5 pl-5">
          <div
            className={`flex mt-2.5 mb-0 min-w-0 ${msg.sender === "user" && "flex-row-reverse ml-auto"}`}
          >
            <img
              src={msg.sender === "user" ? userAvatar : assistantAvatar}
              alt={`${msg.sender} avatar`}
              className="w-[40px] h-[40px] mx-2.5"
            />
            {msg.sender !== "user" ? (
              <TypingChat msg={msg} />
            ) : (
              <Card className="bg-primary">
                <CardBody>{msg.content}</CardBody>
              </Card>
            )}
          </div>
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
}

function InitializingStatus(): JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center m-auto h-full">
      <Loader />
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
      <div className="w-full relative text-base">
        <Textarea
          className="py-4 px-4"
          classNames={{
            input: "pr-16 py-2",
          }}
          value={inputMessage}
          maxRows={10}
          minRows={1}
          variant="bordered"
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Send a message (won't interrupt the Assistant)"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              handleSendMessage();
            }
          }}
        />
        <button
          type="button"
          className="bg-transparent border-none rounded py-2.5 px-5 hover:opacity-80 cursor-pointer select-none absolute right-5 bottom-6"
          onClick={handleSendMessage}
          disabled={!initialized}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
