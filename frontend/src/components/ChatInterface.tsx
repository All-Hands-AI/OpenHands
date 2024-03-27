import React, { useState } from "react";
import { useSelector } from "react-redux";
import assistantAvatar from "../assets/assistant-avatar.png";
import userAvatar from "../assets/user-avatar.png";
import { sendChatMessage } from "../services/chatService";
import { RootState } from "../store";
import "./ChatInterface.css";

function MessageList(): JSX.Element {
  const { messages } = useSelector((state: RootState) => state.chat);
  
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
            <div className="message-content">{msg.content}</div>
          </div>
        </div>
      ))}
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
  );
}

export default ChatInterface;
