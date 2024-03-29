import React, { ChangeEvent, useEffect, useRef, useState } from "react";
import { useSelector } from "react-redux";
import assistantAvatar from "../assets/assistant-avatar.png";
import userAvatar from "../assets/user-avatar.png";
import { sendChatMessage } from "../services/chatService";
import { RootState } from "../store";
import "./css/ChatInterface.css";
import { changeDirectory as sendChangeDirectorySocketMessage } from "../services/settingsService";

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

function DirectoryInput(): JSX.Element {
  const [editing, setEditing] = useState(false);
  const [directory, setDirectory] = useState("Default");

  function save() {
    setEditing(false);
    sendChangeDirectorySocketMessage(directory);
  }

  function onDirectoryInputChange(e: ChangeEvent<HTMLInputElement>) {
    setEditing(true);
    setDirectory(e.target.value);
  }

  return (
    <div className="flex p-2 justify-center gap-2 bg-neutral-700">
      <label htmlFor="directory-input" className="label">
        Directory
      </label>
      <input
        type="text"
        className="input"
        id="directory-input"
        placeholder="Default"
        onChange={onDirectoryInputChange}
      />
      <button
        type="button"
        className={`btn ${editing ? "" : "hidden"}`}
        onClick={save}
      >
        Save
      </button>
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
      <DirectoryInput />
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
