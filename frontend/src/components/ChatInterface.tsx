import React, { useState } from "react";
import "./ChatInterface.css";
import userAvatar from "../assets/user-avatar.png";
import assistantAvatar from "../assets/assistant-avatar.png";

interface Message {
  content: string;
  sender: "user" | "assistant";
}

function ChatInterface(): JSX.Element {
  const [messages, setMessages] = useState<Message[]>([
    {
      content:
        "I want you to setup this project: https://github.com/mckaywrigley/assistant-ui",
      sender: "user",
    },
    {
      content:
        "Got it, I'll get started on setting up the assistant UI project from the GitHub link you provided. I'll update you on my progress.",
      sender: "assistant",
    },
    { content: "Cloned repo from GitHub.", sender: "assistant" },
    { content: "You're doing great! Keep it up :)", sender: "user" },
    {
      content:
        "Thanks! I've cloned the repo and am currently going through the README to make sure we get everything set up right. There's a detailed guide for local setup as well as instructions for hosting it. I'll follow the steps and keep you posted on the progress! If there are any specific configurations or features you want to prioritize, just let me know.",
      sender: "assistant",
    },
    {
      content: "Installed project dependencies using npm.",
      sender: "assistant",
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");

  const handleSendMessage = () => {
    if (inputMessage.trim() !== "") {
      setMessages([...messages, { content: inputMessage, sender: "user" }]);
      setInputMessage("");
    }
  };

  return (
    <div className="chat-interface">
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
        />
        <button type="button" onClick={handleSendMessage}>
          <span className="button-text">Send</span>
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
