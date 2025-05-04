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

  // Only expand the latest segment on mount / whenever `segments` changes
  React.useEffect(() => {
    const init: Record<string, boolean> = {};
    segments.forEach((_, i) => {
      init[i.toString()] = i === segments.length - 1;
    });
    setExpandedSegments(init);
  }, [segments]);

  const toggleSegment = (idx: string) => {
    setExpandedSegments((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const getMessagesForSegment = (
    segmentIds: number[],
    segmentIndex: number,
    totalSegments: number,
    segment: TrajectorySummarySegment
  ): Message[] => {
    console.log(`Debug - Getting messages for segment ${segmentIndex}:`, {
      segmentIds,
      segmentTitle: segment.title,
      totalSegments
    });

    // 0) No IDs ⇒ just evenly split
    if (!segmentIds || segmentIds.length === 0) {
      console.log(`Debug - No IDs for segment ${segmentIndex}, using even split`);
      const per = Math.ceil(messages.length / totalSegments);
      const start = segmentIndex * per;
      const end = Math.min(start + per, messages.length);
      const result = messages.slice(start, end);
      console.log(`Debug - Even split result for segment ${segmentIndex}:`, {
        messageCount: result.length,
        start,
        end
      });
      return result;
    }

    // 1) exact-ID matching
    const byId = messages.filter(
      (m) => m.eventID !== undefined && segmentIds.includes(m.eventID!)
    );
    console.log(`Debug - Exact ID matching for segment ${segmentIndex}:`, {
      matchCount: byId.length,
      messageIDs: byId.map(m => m.eventID)
    });

    if (byId.length > 0) {
      const seen = new Set<string>();
      const unique = byId.filter((m) => {
        const key = `${m.eventID}_${m.type}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      const result = unique.sort(
        (a, b) =>
          messages.findIndex((m) => m === a) -
          messages.findIndex((m) => m === b)
      );
      console.log(`Debug - Exact ID matching result for segment ${segmentIndex}:`, {
        uniqueCount: result.length
      });
      return result;
    }

    // 2) string-ID fallback
    const byStringId = messages.filter((m) => {
      return (
        m.eventID !== undefined &&
        segmentIds.some((id) => String(id) === String(m.eventID))
      );
    });
    console.log(`Debug - String ID fallback for segment ${segmentIndex}:`, {
      matchCount: byStringId.length,
      messageIDs: byStringId.map(m => m.eventID)
    });

    if (byStringId.length > 0) {
      const seen2 = new Set<string>();
      const unique2 = byStringId.filter((m) => {
        const key = `${m.eventID}_${m.type}`;
        if (seen2.has(key)) return false;
        seen2.add(key);
        return true;
      });
      const result = unique2.sort(
        (a, b) =>
          messages.findIndex((m) => m === a) -
          messages.findIndex((m) => m === b)
      );
      console.log(`Debug - String ID fallback result for segment ${segmentIndex}:`, {
        uniqueCount: result.length
      });
      return result;
    }

    // 3) If we still have no matches, try a more lenient approach
    console.log(`Debug - No matches found for segment ${segmentIndex}, trying lenient approach`);
    const agentMessages = messages.filter(m => m.sender === "assistant" && m.type !== undefined);

    if (agentMessages.length > 0) {
      // Take a portion of agent messages based on segment index
      const messagesPerSegment = Math.ceil(agentMessages.length / totalSegments);
      const start = segmentIndex * messagesPerSegment;
      const end = Math.min(start + messagesPerSegment, agentMessages.length);
      const result = agentMessages.slice(start, end);
      console.log(`Debug - Lenient approach result for segment ${segmentIndex}:`, {
        messageCount: result.length,
        start,
        end
      });
      return result;
    }

    // 3) timestamp-range matching
    if (
      (segment.start_timestamp && segment.end_timestamp) ||
      segment.timestamp_range
    ) {
      let startTime: number | undefined;
      let endTime: number | undefined;
      try {
        if (segment.start_timestamp && segment.end_timestamp) {
          startTime = new Date(
            `2000-01-01 ${segment.start_timestamp}`
          ).getTime();
          endTime = new Date(`2000-01-01 ${segment.end_timestamp}`).getTime();
        } else if (segment.timestamp_range) {
          const [s, e] = segment.timestamp_range.split("-");
          if (s && e) {
            startTime = new Date(`2000-01-01 ${s.trim()}`).getTime();
            endTime = new Date(`2000-01-01 ${e.trim()}`).getTime();
          }
        }
      } catch {
        startTime = endTime = undefined;
      }

      if (startTime !== undefined && endTime !== undefined) {
        const tsMatched = messages.filter((m) => {
          if (!m.timestamp) return false;
          let t: number;
          try {
            t = new Date(m.timestamp).getTime();
          } catch {
            const match = m.timestamp.match(
              /(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?/
            );
            if (!match) return false;
            const [, hh, mm, ss = "0"] = match;
            t = new Date(`2000-01-01 ${hh}:${mm}:${ss}`).getTime();
          }
          return t >= startTime! && t <= endTime!;
        });

        if (tsMatched.length > 0) {
          const seen3 = new Set<string>();
          const unique3 = tsMatched.filter((m) => {
            const key = `${m.eventID}_${m.type}`;
            if (seen3.has(key)) return false;
            seen3.add(key);
            return true;
          });
          return unique3.sort(
            (a, b) =>
              messages.findIndex((m) => m === a) -
              messages.findIndex((m) => m === b)
          );
        }
      }
    }

    // 4) timestamp-only fallback
    if (segment.timestamp_range) {
      const pos = totalSegments > 1 ? segmentIndex / (totalSegments - 1) : 0;
      const startIdx = Math.floor(pos * messages.length * 0.5);
      const endIdx = Math.min(
        startIdx + Math.ceil(messages.length / totalSegments),
        messages.length
      );
      // … if you really want this split, you could dedupe+sort here too …
      return messages.slice(startIdx, endIdx);
    }

    // 5) single segment ⇒ all
    if (totalSegments === 1) return messages;

    // fallback: nothing
    return [];
  };

  // Find all message IDs that are included in segments
  const summarizedIds = React.useMemo(() => {
    const ids = new Set<number>();
    segments.forEach(segment => {
      if (segment.ids && Array.isArray(segment.ids)) {
        segment.ids.forEach(id => {
          if (typeof id === 'number') {
            ids.add(id);
          } else if (typeof id === 'string') {
            // Handle string IDs too, convert to number if possible
            const numId = Number(id);
            if (!isNaN(numId)) {
              ids.add(numId);
            }
          }
        });
      }
    });
    console.log("Debug - Summarized IDs:", Array.from(ids));
    return ids;
  }, [segments]);

  // Organize messages by their position in the original message list
  const organizedContent = React.useMemo(() => {
    // Store segments by their start timestamp or first message index for ordering
    const segmentPositions = segments.map((segment, idx) => {
      // Get the messages for this segment
      const segmentMessages = getMessagesForSegment(
        segment.ids || [],
        idx,
        segments.length,
        segment
      );

      // Find the index of the first message in this segment
      let firstMessageIndex = Infinity;
      if (segmentMessages.length > 0) {
        segmentMessages.forEach(msg => {
          const msgIndex = messages.findIndex(m => m.eventID === msg.eventID);
          if (msgIndex !== -1 && msgIndex < firstMessageIndex) {
            firstMessageIndex = msgIndex;
          }
        });
      } else if (segment.start_timestamp) {
        // Use timestamp as fallback for ordering
        firstMessageIndex = idx * 1000; // Just to ensure some ordering
      } else {
        // No messages or timestamp, use segment index for ordering
        firstMessageIndex = idx * 1000;
      }

      return {
        segmentIndex: idx,
        firstMessageIndex: firstMessageIndex !== Infinity ? firstMessageIndex : idx * 1000,
        segment,
        messages: segmentMessages
      };
    });

    // Sort segments by their position in the original message flow
    segmentPositions.sort((a, b) => a.firstMessageIndex - b.firstMessageIndex);

    // Find the first user message for special display
    const firstUserMessage = messages.find(msg => msg.sender === "user");

    // Find messages not included in any segment
    const unsummarizedMessages = messages.filter(msg => {
      return !msg.eventID || !summarizedIds.has(msg.eventID);
    });

    console.log("Debug - Organized content:", {
      segmentCount: segmentPositions.length,
      unsummarizedCount: unsummarizedMessages.length,
      hasFirstUserMessage: !!firstUserMessage
    });

    return {
      firstUserMessage,
      segments: segmentPositions,
      unsummarizedMessages
    };
  }, [messages, segments, summarizedIds]);

  // Extract user messages for display before segments
  const userMessages = React.useMemo(
    () => messages.filter((msg) => msg.sender === "user"),
    [messages]
  );

  return (
    <div className="flex flex-col gap-4 w-full">
      {/* Overall Summary - only show if we have segments */}
      {segments.length > 0 && (
        <div className="bg-base-secondary p-4 rounded-lg border border-tertiary">
          <h2 className="text-lg font-semibold mb-2 text-content">
            Conversation Summary
          </h2>
          <p className="text-content">{overallSummary}</p>
        </div>
      )}

      {/* First User Message - Display at the top */}
      {organizedContent.firstUserMessage && (
        <div className="flex flex-col gap-2">
          <ChatMessage
            key="initial-user-message"
            type="user"
            message={organizedContent.firstUserMessage.content}
            id={organizedContent.firstUserMessage.eventID}
          >
            {organizedContent.firstUserMessage.imageUrls &&
             organizedContent.firstUserMessage.imageUrls.length > 0 && (
              <ImageCarousel
                size="small"
                images={organizedContent.firstUserMessage.imageUrls}
              />
            )}
          </ChatMessage>
        </div>
      )}

      {/* Organized Content: Segments in chronological order with unsummarized messages */}
      {organizedContent.segments.map(({ segment, segmentIndex, messages: segmentMessages }) => (
        <div
          key={segmentIndex}
          className="border border-tertiary rounded-lg overflow-hidden"
        >
          <div
            className="bg-base-secondary p-3 flex justify-between items-center cursor-pointer hover:bg-tertiary transition-colors"
            onClick={() => toggleSegment(segmentIndex.toString())}
          >
            <div>
              <h3 className="font-medium text-content">{segment.title}</h3>
              <p className="text-sm text-tertiary-light">
                {segment.timestamp_range}
              </p>
            </div>
            <div className="text-tertiary-light">
              {expandedSegments[segmentIndex.toString()] ? (
                /* Chevron up */
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
                /* Chevron down */
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

          {expandedSegments[segmentIndex.toString()] && (
            <div className="p-3 bg-base">
              <div className="mb-3">
                <p className="text-content">{segment.summary}</p>
              </div>

              <div className="flex flex-col gap-2 mt-4">
                {(() => {
                  if (segmentMessages.length === 0) {
                    return (
                      <div className="text-tertiary-light italic text-sm p-2">
                        No messages found for this segment.
                      </div>
                    );
                  }

                  return segmentMessages.map((msg, mi) => {
                    const showConfirm =
                      mi === segmentMessages.length - 1 &&
                      msg.sender === "assistant" &&
                      isAwaitingUserConfirmation;

                    if (msg.type === "error" || msg.type === "action") {
                      return (
                        <div key={mi} className="text-content">
                          {msg.thought && (
                            <ChatMessage
                              type="assistant"
                              message={msg.thought}
                              id={msg.eventID}
                            />
                          )}
                          <ExpandableMessage
                            type={msg.type}
                            id={msg.translationID}
                            message={msg.content}
                            success={msg.success}
                            eventID={msg.eventID}
                          />
                          {showConfirm && <ConfirmationButtons />}
                        </div>
                      );
                    }

                    return (
                      <ChatMessage
                        key={mi}
                        type={msg.sender}
                        message={msg.content}
                        id={msg.eventID}
                      >
                        {msg.imageUrls && msg.imageUrls.length > 0 && (
                          <ImageCarousel size="small" images={msg.imageUrls} />
                        )}
                        {showConfirm && <ConfirmationButtons />}
                      </ChatMessage>
                    );
                  });
                })()}
              </div>
            </div>
          )}
        </div>
      ))}

      {/* Display unsummarized messages ONLY if they aren't already included in segments */}
      {organizedContent.unsummarizedMessages.length > 0 && (
        <div className="flex flex-col gap-2">
          {organizedContent.unsummarizedMessages.map((msg, idx) => {
            // Skip the first user message as it's already displayed at the top
            if (
              organizedContent.firstUserMessage &&
              msg.eventID === organizedContent.firstUserMessage.eventID
            ) {
              return null;
            }

            const showConfirm =
              messages.length - 1 === messages.indexOf(msg) &&
              msg.sender === "assistant" &&
              isAwaitingUserConfirmation;

            if (msg.type === "error" || msg.type === "action") {
              return (
                <div key={idx} className="text-content">
                  {msg.thought && (
                    <ChatMessage
                      type="assistant"
                      message={msg.thought}
                      id={msg.eventID}
                    />
                  )}
                  <ExpandableMessage
                    type={msg.type}
                    id={msg.translationID}
                    message={msg.content}
                    success={msg.success}
                    eventID={msg.eventID}
                  />
                  {showConfirm && <ConfirmationButtons />}
                </div>
              );
            }

            return (
              <ChatMessage
                key={idx}
                type={msg.sender}
                message={msg.content}
                id={msg.eventID}
              >
                {msg.imageUrls && msg.imageUrls.length > 0 && (
                  <ImageCarousel size="small" images={msg.imageUrls} />
                )}
                {showConfirm && <ConfirmationButtons />}
              </ChatMessage>
            );
          })}
        </div>
      )}
    </div>
  );
}
