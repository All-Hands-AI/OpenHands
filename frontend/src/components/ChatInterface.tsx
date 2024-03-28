import React, { useEffect, useRef, useState } from "react";
import { useSelector } from "react-redux";
import "./ChatInterface.css";
import userAvatar from "../assets/user-avatar.png";
import assistantAvatar from "../assets/assistant-avatar.png";
import { RootState } from "../store";
import { sendChatMessage } from "../services/chatService";

function MessageList(): JSX.Element {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages } = useSelector((state: RootState) => state.chat);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="message-list">
      {messages.map((msg, index) => (
        <div key={index} className="message-layout">
          <div
            className={`${msg.sender === "user" ? "user-message" : "message"}`}
          >
            <img
              src={msg.sender === "user" ? userAvatar : assistantAvatar}
              alt={`${msg.sender} avatar`}
              className="avatar"
            />
            <div className="chat chat-bubble">{msg.content}</div>
          </div>
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
}

function InitializingStatus(): JSX.Element {
  return (
    <div className="initializing-status">
      <img src={assistantAvatar} alt="assistant avatar" className="avatar" />
      <div>Initializing agent (may take up to 10 seconds)...</div>
    </div>
  );
}

function ChatInterface(): JSX.Element {
  const { initialized } = useSelector((state: RootState) => state.task);
  const [inputMessage, setInputMessage] = useState("");

  const handleSendMessage = () => {
    if (inputMessage.trim() !== "") {
      sendChatMessage(inputMessage);
      setInputMessage("");
    }
  };

  return (
    <div className="chat-interface">
      {initialized ? <MessageList /> : <InitializingStatus />}
      <div className="input-container">
        <div className="input-box">
          <input
            type="text"
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
            onClick={handleSendMessage}
            disabled={!initialized}
          >
            <span className="button-text">Send</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;
