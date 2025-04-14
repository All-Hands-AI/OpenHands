import { DynamicText } from "#/components/DynamicText"
import { ChatMessage } from "#/components/features/chat/chat-message"
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons"
import { Stepper } from "#/components/Stepper"
import type { Message } from "#/message"
import { cn } from "#/utils/utils"
import React, { useEffect, useState } from "react"
import { ImageCarousel } from "../images/image-carousel"
import videoSrc from "./agents-building-w-bg-animated.mp4"
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

      const texts = [
        "Warming up the engines… Thank you for your patience!",
        "Hang tight, we’re working our magic…",
        "Pro tip: Great answers take time!",
        "Almost there – just booting up the AI brain…",
      ]

      if (message.type === "customAction") {
        return (
          <div key={index} className={cn(messageClass)}>
            <div className="mb-4 flex w-[600px] items-center justify-center rounded-[20px] rounded-br-none bg-white">
              <Stepper currentStep={1} />
            </div>

            <div className="max-w-[522px] rounded-[20px] rounded-br-none bg-white p-4">
              <div className="flex items-center justify-center">
                <video
                  preload="auto"
                  // ref={videoRef}
                  muted={true}
                  autoPlay
                  playsInline
                  loop
                  controls={false}
                  width={200}
                  height={200}
                  className="rounded-[20px]"
                >
                  <source src={videoSrc} type="video/mp4" />
                  <track kind="captions" />
                </video>
              </div>
              <DynamicText items={texts} />
            </div>
          </div>
        )
      }

      return (
        <ChatMessage
          key={index}
          type={message.sender}
          message={message.content}
          className={messageClass}
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
