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
          <div key={index} className="message">
            <img
              src={msg.sender === "user" ? userAvatar : assistantAvatar}
              alt={`${msg.sender} avatar`}
              className="avatar"
            />
            <div className="message-content">{msg.content}</div>
          </div>
        ))}
      </div>
      <div className="input-container">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Send a message (won't interrupt the Assistant)"
        />
        <button type="button" onClick={handleSendMessage}>
          <span className="button-text">Send</span>
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
