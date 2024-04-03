import { Card, CardBody, Textarea } from "@nextui-org/react";
import React, { useEffect, useRef, useState } from "react";
import { useSelector } from "react-redux";
import assistantAvatar from "../assets/assistant-avatar.png";
import CogTooth from "../assets/cog-tooth";
import userAvatar from "../assets/user-avatar.png";
import { useTypingEffect } from "../hooks/useTypingEffect";
import {
  sendChatMessage,
  setCurrentQueueMarkerState,
  setCurrentTypingMsgState,
  setTypingAcitve,
  addAssistanctMessageToChat,
} from "../services/chatService";
import { RootState } from "../store";
import { Message } from "../state/chatSlice";

interface IChatBubbleProps {
  msg: Message;
}

/**
 * @returns jsx
 *
 * component used for typing effect when assistant replies
 *
 * makes uses of useTypingEffect hook
 *
 */
function TypingChat() {
  const { currentTypingMessage, currentQueueMarker, queuedTyping, messages } =
    useSelector((state: RootState) => state.chat);

  return (
    // eslint-disable-next-line react/jsx-no-useless-fragment
    <>
      {currentQueueMarker !== null && (
        <Card className="bg-success-100">
          <CardBody>
            {useTypingEffect([currentTypingMessage], {
              loop: false,
              setTypingAcitve,
              setCurrentQueueMarkerState,
              currentQueueMarker,
              playbackRate: 0.1,
              addAssistanctMessageToChat,
              assistantMessageObj: messages?.[queuedTyping[currentQueueMarker]],
            })}
          </CardBody>
        </Card>
      )}
    </>
  );
}

function ChatBubble({ msg }: IChatBubbleProps): JSX.Element {
  return (
    <div className="flex mb-2.5 pr-5 pl-5">
      <div
        className={`flex mt-2.5 mb-0 min-w-0 ${msg?.sender === "user" && "flex-row-reverse ml-auto"}`}
      >
        <img
          src={msg?.sender === "user" ? userAvatar : assistantAvatar}
          alt={`${msg?.sender} avatar`}
          className="w-[40px] h-[40px] mx-2.5"
        />
        <Card className={`${msg?.sender === "user" ? "bg-primary-100" : ""}`}>
          <CardBody>{msg?.content}</CardBody>
        </Card>
      </div>
    </div>
  );
}

function MessageList(): JSX.Element {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const {
    messages,
    queuedTyping,
    typingActive,
    currentQueueMarker,
    currentTypingMessage,
    newChatSequence,
  } = useSelector((state: RootState) => state.chat);

  const messageScroll = () => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  };

  useEffect(() => {
    messageScroll();
    if (!typingActive) return;

    const interval = setInterval(() => {
      messageScroll();
    }, 1000);

    // eslint-disable-next-line consistent-return
    return () => clearInterval(interval);
  }, [newChatSequence, typingActive]);

  useEffect(() => {
    const newMessage = messages?.[queuedTyping[currentQueueMarker]]?.content;

    if (
      currentQueueMarker !== null &&
      currentQueueMarker !== 0 &&
      currentTypingMessage !== newMessage
    ) {
      setCurrentTypingMsgState(
        messages?.[queuedTyping?.[currentQueueMarker]]?.content,
      );
    }
  }, [queuedTyping]);

  useEffect(() => {
    if (currentTypingMessage === "") return;

    if (!typingActive) setTypingAcitve(true);
  }, [currentTypingMessage]);

  useEffect(() => {
    const newMessage = messages?.[queuedTyping[currentQueueMarker]]?.content;
    if (
      newMessage &&
      typingActive === false &&
      currentTypingMessage !== newMessage
    ) {
      if (currentQueueMarker !== 0) {
        setCurrentTypingMsgState(
          messages?.[queuedTyping?.[currentQueueMarker]]?.content,
        );
      }
    }
  }, [typingActive]);

  useEffect(() => {
    if (currentQueueMarker === 0) {
      setCurrentTypingMsgState(messages?.[queuedTyping?.[0]]?.content);
    }
  }, [currentQueueMarker]);

  return (
    <div className="flex-1 overflow-y-auto">
      {newChatSequence.map((msg, index) =>
        // eslint-disable-next-line no-nested-ternary
        msg.sender === "user" || msg.sender === "assistant" ? (
          <ChatBubble key={index} msg={msg} />
        ) : (
          <div key={index} />
        ),
      )}

      {typingActive && (
        <div className="flex mb-2.5 pr-5 pl-5 bg-s">
          <div className="flex mt-2.5 mb-0 min-w-0 ">
            <img
              src={assistantAvatar}
              alt="assistant avatar"
              className="w-[40px] h-[40px] mx-2.5"
            />
            <TypingChat />
          </div>
        </div>
      )}
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
          onChange={(e) =>
            e.target.value !== "\n" && setInputMessage(e.target.value)
          }
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
