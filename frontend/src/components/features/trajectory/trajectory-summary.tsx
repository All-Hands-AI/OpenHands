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

export function TrajectorySummary({
  overallSummary,
  segments,
  messages,
  isAwaitingUserConfirmation,
}: TrajectorySummaryProps) {
  const [expandedSegments, setExpandedSegments] = React.useState<
    Record<string, boolean>
  >({});

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
  const getMessagesForSegment = (
    segmentIds: number[],
    segmentIndex: number,
    totalSegments: number,
    segment: TrajectorySummarySegment,
  ) => {
    // If no segment IDs are provided, try to estimate which messages belong to this segment
    if (!segmentIds || segmentIds.length === 0) {
      // If we have no IDs, try to divide messages evenly among segments
      const messagesPerSegment = Math.ceil(messages.length / totalSegments);
      const startIdx = segmentIndex * messagesPerSegment;
      const endIdx = Math.min(startIdx + messagesPerSegment, messages.length);

      return messages.slice(startIdx, endIdx);
    }

    // First try to match by exact event ID
    const matchedMessages = messages.filter((message) => {
      const messageId = message.eventID;
      return messageId !== undefined && segmentIds.includes(messageId);
    });

    // If we found messages, return them
    if (matchedMessages.length > 0) {
      // Find all message IDs in this segment
      const numericIds = segmentIds.filter(id => typeof id === 'number');
      
      if (numericIds.length > 1) {
        // Get the min and max IDs to include all messages between them
        const minId = Math.min(...numericIds);
        const maxId = Math.max(...numericIds);
        
        // Return all messages with IDs in the range [minId, maxId]
        return messages.filter(msg => {
          const id = msg.eventID;
          return id !== undefined && id >= minId && id <= maxId;
        });
      } else {
        // If we only have one numeric ID or none, use the original approach
        // Sort messages by their original order in the messages array
        const messageIndices = matchedMessages.map(msg => 
          messages.findIndex(m => m.eventID === msg.eventID)
        );
        
        // Get the min and max indices to include all messages between them
        const minIndex = Math.min(...messageIndices);
        const maxIndex = Math.max(...messageIndices);
        
        // Return all messages between min and max indices to include the complete conversation
        return messages.slice(minIndex, maxIndex + 1);
      }
    }

    // If no messages were found by exact ID match, try to match by string conversion
    // This handles cases where IDs might be stored as strings in one place and numbers in another
    const stringMatchedMessages = messages.filter((message) => {
      const messageId = message.eventID;
      if (messageId === undefined) return false;

      // Try to match by converting both to strings
      return segmentIds.some((id) => String(id) === String(messageId));
    });

    if (stringMatchedMessages.length > 0) {
      // Try to convert string IDs to numbers for comparison
      const numericIds = segmentIds
        .map(id => {
          if (typeof id === 'number') return id;
          if (typeof id === 'string' && !isNaN(Number(id))) return Number(id);
          return null;
        })
        .filter(id => id !== null) as number[];
      
      if (numericIds.length > 1) {
        // Get the min and max IDs to include all messages between them
        const minId = Math.min(...numericIds);
        const maxId = Math.max(...numericIds);
        
        // Return all messages with IDs in the range [minId, maxId]
        return messages.filter(msg => {
          const id = msg.eventID;
          return id !== undefined && id >= minId && id <= maxId;
        });
      } else {
        // If we only have one numeric ID or none, use the original approach
        // Get the indices of each matched message in the original messages array
        const messageIndices = stringMatchedMessages.map(msg => 
          messages.findIndex(m => m === msg)
        );
        
        // Get the min and max indices to include all messages between them
        const minIndex = Math.min(...messageIndices);
        const maxIndex = Math.max(...messageIndices);
        
        // Return all messages between min and max indices to include the complete conversation
        return messages.slice(minIndex, maxIndex + 1);
      }
    }

    // If we still couldn't find any messages, try to use timestamp ranges if available
    if (
      (segment.start_timestamp && segment.end_timestamp) ||
      segment.timestamp_range
    ) {
      let startTime;
      let endTime;

      try {
        // First try to use the start_timestamp and end_timestamp directly
        if (segment.start_timestamp && segment.end_timestamp) {
          startTime = new Date(
            `2000-01-01 ${segment.start_timestamp}`,
          ).getTime();
          endTime = new Date(`2000-01-01 ${segment.end_timestamp}`).getTime();
        } else if (segment.timestamp_range) {
          // If that fails, try to extract from timestamp_range
          const [startStr, endStr] = segment.timestamp_range.split("-");
          if (startStr && endStr) {
            startTime = new Date(`2000-01-01 ${startStr.trim()}`).getTime();
            endTime = new Date(`2000-01-01 ${endStr.trim()}`).getTime();
          }
        }
      } catch (e) {
        // If parsing fails, we can't match by timestamp
        startTime = undefined;
        endTime = undefined;
      }

      if (startTime && endTime) {
        const timestampFilteredMessages = messages.filter((message) => {
          if (!message.timestamp) return false;

          // Convert message timestamp to comparable format
          let msgTime;
          try {
            msgTime = new Date(message.timestamp).getTime();
          } catch (e) {
            // If parsing fails, try to extract just the time part
            const timeMatch = message.timestamp.match(
              /(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?/,
            );
            if (timeMatch) {
              const [, hours, minutes, seconds = "0"] = timeMatch;
              msgTime = new Date(
                `2000-01-01 ${hours}:${minutes}:${seconds}`,
              ).getTime();
            } else {
              return false;
            }
          }

          return msgTime >= startTime && msgTime <= endTime;
        });

        if (timestampFilteredMessages.length > 0) {
          // Try to find message IDs in the filtered messages
          const messageIds = timestampFilteredMessages
            .map(msg => msg.eventID)
            .filter(id => id !== undefined) as number[];
          
          if (messageIds.length > 1) {
            // Get the min and max IDs to include all messages between them
            const minId = Math.min(...messageIds);
            const maxId = Math.max(...messageIds);
            
            // Return all messages with IDs in the range [minId, maxId]
            return messages.filter(msg => {
              const id = msg.eventID;
              return id !== undefined && id >= minId && id <= maxId;
            });
          } else {
            // If we don't have enough message IDs, use the original approach
            // Find the indices of the first and last matching messages
            const messageIndices = timestampFilteredMessages.map(msg => 
              messages.findIndex(m => m === msg)
            );
            
            // Get the min and max indices to include all messages between them
            const minIndex = Math.min(...messageIndices);
            const maxIndex = Math.max(...messageIndices);
            
            // Return all messages between min and max indices to include the complete conversation
            return messages.slice(minIndex, maxIndex + 1);
          }
        }
      }
    }

    // If we have a timestamp range but couldn't match any messages, try to estimate based on the segment index
    if (segment.timestamp_range) {
      // Calculate approximate position in the message array based on segment index
      const segmentPosition =
        totalSegments > 1 ? segmentIndex / (totalSegments - 1) : 0; // 0 to 1
      const startIdx = Math.floor(segmentPosition * messages.length * 0.5); // Start at half the proportional position
      const endIdx = Math.min(
        startIdx + Math.ceil(messages.length / totalSegments),
        messages.length,
      );

      return messages.slice(startIdx, endIdx);
    }

    // If there's only one segment, return all messages
    if (totalSegments === 1) {
      return messages;
    }

    // If all else fails, return an empty array
    return [];
  };

  return (
    <div className="flex flex-col gap-4 w-full">
      {/* Overall Summary */}
      <div className="bg-base-secondary p-4 rounded-lg border border-tertiary">
        <h2 className="text-lg font-semibold mb-2 text-content">
          Conversation Summary
        </h2>
        <p className="text-content">{overallSummary}</p>
      </div>

      {/* Segments */}
      {segments.map((segment, index) => (
        <div
          key={index}
          className="border border-tertiary rounded-lg overflow-hidden"
        >
          {/* Segment Header */}
          <div
            className="bg-base-secondary p-3 flex justify-between items-center cursor-pointer hover:bg-tertiary transition-colors"
            onClick={() => toggleSegment(index.toString())}
          >
            <div>
              <h3 className="font-medium text-content">{segment.title}</h3>
              <p className="text-sm text-tertiary-light">
                {segment.timestamp_range}
              </p>
            </div>
            <div className="text-tertiary-light">
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
            <div className="p-3 bg-base">
              <div className="mb-3">
                <p className="text-content">{segment.summary}</p>
              </div>

              {/* Messages in this segment */}
              <div className="flex flex-col gap-2 mt-4">
                {(() => {
                  const segmentMessages = getMessagesForSegment(
                    segment.ids,
                    index,
                    segments.length,
                    segment,
                  );
                  
                  // Debug: Log segment information
                  console.log(`Segment ${index} - ${segment.title}:`, {
                    ids: segment.ids,
                    timestamp_range: segment.timestamp_range,
                    messageCount: segmentMessages.length,
                    messages: segmentMessages.map(m => ({
                      id: m.eventID,
                      sender: m.sender,
                      content: m.content?.substring(0, 50) + (m.content?.length > 50 ? '...' : '')
                    }))
                  });
                  
                  // Additional debugging to check for missing messages
                  const allMessageIds = messages.map(m => m.eventID);
                  const segmentMessageIds = segmentMessages.map(m => m.eventID);
                  const missingIds = segment.ids.filter(id => 
                    !segmentMessageIds.includes(id) && allMessageIds.includes(id)
                  );
                  
                  if (missingIds.length > 0) {
                    console.warn(`Segment ${index} is missing messages with IDs:`, missingIds);
                    console.warn(`Messages that should be included:`, 
                      messages.filter(m => missingIds.includes(m.eventID))
                        .map(m => ({
                          id: m.eventID,
                          sender: m.sender,
                          content: m.content?.substring(0, 50) + (m.content?.length > 50 ? '...' : '')
                        }))
                    );
                  }

                  if (segmentMessages.length === 0) {
                    return (
                      <div className="text-tertiary-light italic text-sm p-2">
                        No messages found for this segment. This may be due to
                        missing message IDs in the summary.
                      </div>
                    );
                  }

                  return segmentMessages.map((message, msgIndex) => {
                    const shouldShowConfirmationButtons =
                      messages.length - 1 === msgIndex &&
                      message.sender === "assistant" &&
                      isAwaitingUserConfirmation;

                    if (message.type === "error" || message.type === "action") {
                      return (
                        <div key={msgIndex} className="text-content">
                          <ExpandableMessage
                            type={message.type}
                            id={message.translationID}
                            message={message.content}
                            success={message.success}
                          />
                          {shouldShowConfirmationButtons && (
                            <ConfirmationButtons />
                          )}
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
                          <ImageCarousel
                            size="small"
                            images={message.imageUrls}
                          />
                        )}
                        {shouldShowConfirmationButtons && (
                          <ConfirmationButtons />
                        )}
                      </ChatMessage>
                    );
                  });
                })()}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
