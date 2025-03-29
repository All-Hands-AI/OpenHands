import React, { useState, useEffect } from "react";
import type { Message } from "#/message";
import { ChatMessage } from "#/components/features/chat/chat-message";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";
import { ImageCarousel } from "../images/image-carousel";
import { ExpandableMessage } from "./expandable-message";

interface MessagesProps {
  messages: Message[];
  isAwaitingUserConfirmation: boolean;
}

enum IconBackgroundColor {
  RED = "bg-red-600",
  BLUE = "bg-blue-600",
  GREEN = "bg-green-600",
  ORANGE = "bg-orange-600",
  SKY = "bg-sky-600",
  YELLOW = "bg-yellow-600",
  PINK = "bg-pink-600",
  CYAN = "bg-cyan-600",
  PURPLE = "bg-purple-600",
}

export const Messages: React.FC<MessagesProps> = React.memo(
  ({ messages, isAwaitingUserConfirmation }) => {
    const [receivedAgentNames, setAgentNames] = useState<string[]>([]);
    const iconColors = Object.values(IconBackgroundColor);

    useEffect(() => {
      const newAgentNames = messages
        .map((message) => message.agentName)
        .filter(
          (name): name is string =>
            !!name && !receivedAgentNames.includes(name),
        );
      if (newAgentNames.length > 0) {
        setAgentNames((prev) => [...prev, ...newAgentNames]);
      }
    }, [messages]);

    return messages.map((message, index) => {
      if (!message.content) {
        return null;
      }
      const shouldShowConfirmationButtons =
        messages.length - 1 === index &&
        message.sender === "assistant" &&
        isAwaitingUserConfirmation;

      let agentDisplayName = "";
      let agentInitial = "";
      let agentBgColor = iconColors[0];
      if (message.agentName) {
        const agentIndex = Math.max(
          receivedAgentNames.indexOf(message.agentName),
          0,
        );
        const colorIndex = agentIndex % iconColors.length;
        agentBgColor = iconColors[colorIndex];
        agentDisplayName = message.agentName;
      } else {
        agentDisplayName = "Agent";
      }
      agentInitial = agentDisplayName.charAt(0).toUpperCase();

      if (message.type === "error" || message.type === "action") {
        return (
          <div key={index}>
            <ExpandableMessage
              type={message.type}
              id={message.translationID}
              message={message.content}
              success={message.success}
              timestamp={message.timestamp}
              sender={message.sender}
              agentName={message.agentName}
              agentBgColor={agentBgColor}
            />
            {shouldShowConfirmationButtons && <ConfirmationButtons />}
          </div>
        );
      }

      let timestampDisplay = "N/A";
      if (message.timestamp) {
        const date = new Date(
          message.timestamp.endsWith("Z")
            ? message.timestamp
            : `${message.timestamp}Z`,
        );

        const pad = (num: number): string => num.toString().padStart(2, "0");
        const month = pad(date.getMonth() + 1);
        const day = pad(date.getDate());
        const hour = pad(date.getHours());
        const minute = pad(date.getMinutes());
        timestampDisplay = `${month}/${day} ${hour}:${minute}`;
      }

      return (
        <div
          key={index}
          className={message.sender === "assistant" ? "assistant" : "user"}
        >
          {(() => {
            if (message.sender === "assistant") {
              return (
                <div className="agent-info">
                  <div className={`common-icon ${agentBgColor}`}>
                    {agentInitial}
                  </div>
                  <div className="agent-name">{agentDisplayName}</div>
                  <div className="agent-time">{timestampDisplay}</div>
                </div>
              );
            }
            if (message.sender === "user") {
              return (
                <div>
                  <div className="user-time">{timestampDisplay}</div>
                </div>
              );
            }
            return null;
          })()}
          <ChatMessage type={message.sender} message={message.content}>
            {message.imageUrls && message.imageUrls.length > 0 && (
              <ImageCarousel size="small" images={message.imageUrls} />
            )}
            {shouldShowConfirmationButtons && <ConfirmationButtons />}
          </ChatMessage>
        </div>
      );
    });
  },
);

Messages.displayName = "Messages";
