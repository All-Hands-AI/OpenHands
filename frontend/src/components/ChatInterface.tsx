import React, { useState } from "react";
import { useSelector } from "react-redux";
import "./ChatInterface.css";
import userAvatar from "../assets/user-avatar.png";
import assistantAvatar from "../assets/assistant-avatar.png";
import { RootState } from "../store";
import { sendChatMessage } from "../services/chatService";

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
        <button className="attach-button" type="button" aria-label="file">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              fillRule="evenodd"
              clipRule="evenodd"
              d="M9 7C9 4.23858 11.2386 2 14 2C16.7614 2 19 4.23858 19 7V15C19 18.866 15.866 22 12 22C8.13401 22 5 18.866 5 15V9C5 8.44772 5.44772 8 6 8C6.55228 8 7 8.44772 7 9V15C7 17.7614 9.23858 20 12 20C14.7614 20 17 17.7614 17 15V7C17 5.34315 15.6569 4 14 4C12.3431 4 11 5.34315 11 7V15C11 15.5523 11.4477 16 12 16C12.5523 16 13 15.5523 13 15V9C13 8.44772 13.4477 8 14 8C14.5523 8 15 8.44772 15 9V15C15 16.6569 13.6569 18 12 18C10.3431 18 9 16.6569 9 15V7Z"
              fill="currentColor"
            />
          </svg>
        </button>
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
          disabled={!initialized}
        />
        <button type="button" onClick={handleSendMessage}>
          <span className="button-text">Send</span>
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
