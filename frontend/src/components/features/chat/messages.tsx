import { ChatMessage } from "#/components/features/chat/chat-message"
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons"
import type { Message } from "#/message"
import React, { useEffect, useState } from "react"
import { ImageCarousel } from "../images/image-carousel"
import { ExpandableMessage } from "./expandable-message"

interface MessagesProps {
  messages: Message[]
  isAwaitingUserConfirmation: boolean
}

export const Messages: React.FC<MessagesProps> = React.memo(
  ({ messages, isAwaitingUserConfirmation }) => {
    const [latestTimestamp, setLatestTimestamp] = useState<string | null>(null)

    useEffect(() => {
      if (messages.length > 0) {
        const newestMessage = messages.reduce((prev, current) =>
          new Date(current.timestamp) > new Date(prev.timestamp)
            ? current
            : prev,
        )
        setLatestTimestamp(newestMessage.timestamp)
      }
    }, [messages])

    return messages.map((message, index) => {
      const isLatestMessage = message.timestamp === latestTimestamp
      const messageClass = isLatestMessage ? "message-fade-in" : ""

      const shouldShowConfirmationButtons =
        messages.length - 1 === index &&
        message.sender === "assistant" &&
        isAwaitingUserConfirmation

      if (message.type === "error" || message.type === "action") {
        return (
          <div key={index} className={messageClass}>
            <ExpandableMessage
              type={message.type}
              id={message.translationID}
              message={message.content}
              success={message.success}
              messageActionID={message.messageActionID}
              eventID={message.eventID}
              observation={message.observation}
              action={message.action}
            />
            {shouldShowConfirmationButtons && <ConfirmationButtons />}
          </div>
        )
      }

      return (
        <ChatMessage
          key={index}
          type={message.sender}
          message={message.content}
          className={messageClass}
          messageLength={messages.length}
        >
          {message.imageUrls && message.imageUrls.length > 0 && (
            <ImageCarousel size="small" images={message.imageUrls} />
          )}
          {shouldShowConfirmationButtons && <ConfirmationButtons />}
        </ChatMessage>
      )
    })
  },
)
