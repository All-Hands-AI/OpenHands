import React from "react";
import { TrajectorySummarySegment } from "#/api/open-hands.types";
import { Message } from "#/message";
import { ChatMessage } from "#/components/features/chat/chat-message";
import { ExpandableMessage } from "#/components/features/chat/expandable-message";
import { ImageCarousel } from "../images/image-carousel";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";

interface TrajectorySummaryProps {
  overallSummary: string;
  segments: TrajectorySummarySegment[];
  messages: Message[];
  isAwaitingUserConfirmation: boolean;
}

export const TrajectorySummary: React.FC<TrajectorySummaryProps> = ({
  overallSummary,
  segments,
  messages,
  isAwaitingUserConfirmation,
}) => {
  const [expandedSegments, setExpandedSegments] = React.useState<Record<string, boolean>>({});

  // Initialize all segments as expanded
  React.useEffect(() => {
    const initialExpandedState: Record<string, boolean> = {};
    segments.forEach((segment, index) => {
      initialExpandedState[index.toString()] = true;
    });
    setExpandedSegments(initialExpandedState);
  }, [segments]);

  const toggleSegment = (index: string) => {
    setExpandedSegments((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  // Group messages by segment
  const getMessagesForSegment = (segmentIds: number[]) => {
    return messages.filter((message) => {
      const messageId = message.eventID;
      return messageId !== undefined && segmentIds.includes(messageId);
    });
  };

  return (
    <div className="flex flex-col gap-4 w-full">
      {/* Overall Summary */}
      <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Conversation Summary</h2>
        <p className="text-gray-700 dark:text-gray-300">{overallSummary}</p>
      </div>

      {/* Segments */}
      {segments.map((segment, index) => (
        <div
          key={index}
          className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
        >
          {/* Segment Header */}
          <div
            className="bg-gray-100 dark:bg-gray-800 p-3 flex justify-between items-center cursor-pointer"
            onClick={() => toggleSegment(index.toString())}
          >
            <div>
              <h3 className="font-medium">{segment.title}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {segment.timestamp_range}
              </p>
            </div>
            <div className="text-gray-500 dark:text-gray-400">
              {expandedSegments[index.toString()] ? (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </div>
          </div>

          {/* Segment Content */}
          {expandedSegments[index.toString()] && (
            <div className="p-3">
              <div className="mb-3">
                <p className="text-gray-700 dark:text-gray-300">{segment.summary}</p>
              </div>

              {/* Messages in this segment */}
              <div className="flex flex-col gap-2 mt-4">
                {getMessagesForSegment(segment.ids).map((message, msgIndex) => {
                  const shouldShowConfirmationButtons =
                    messages.length - 1 === msgIndex &&
                    message.sender === "assistant" &&
                    isAwaitingUserConfirmation;

                  if (message.type === "error" || message.type === "action") {
                    return (
                      <div key={msgIndex}>
                        <ExpandableMessage
                          type={message.type}
                          id={message.translationID}
                          message={message.content}
                          success={message.success}
                        />
                        {shouldShowConfirmationButtons && <ConfirmationButtons />}
                      </div>
                    );
                  }

                  return (
                    <ChatMessage
                      key={msgIndex}
                      type={message.sender}
                      message={message.content}
                    >
                      {message.imageUrls && message.imageUrls.length > 0 && (
                        <ImageCarousel size="small" images={message.imageUrls} />
                      )}
                      {shouldShowConfirmationButtons && <ConfirmationButtons />}
                    </ChatMessage>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
