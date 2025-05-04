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
    // 0) No IDs ⇒ just evenly split
    if (!segmentIds || segmentIds.length === 0) {
      const per = Math.ceil(messages.length / totalSegments);
      const start = segmentIndex * per;
      const end = Math.min(start + per, messages.length);
      return messages.slice(start, end);
    }

    // 1) exact-ID matching
    const byId = messages.filter(
      (m) => m.eventID !== undefined && segmentIds.includes(m.eventID!)
    );
    if (byId.length > 0) {
      const seen = new Set<string>();
      const unique = byId.filter((m) => {
        const key = `${m.eventID}_${m.type}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      return unique.sort(
        (a, b) =>
          messages.findIndex((m) => m === a) -
          messages.findIndex((m) => m === b)
      );
    }

    // 2) string-ID fallback
    const byStringId = messages.filter((m) => {
      return (
        m.eventID !== undefined &&
        segmentIds.some((id) => String(id) === String(m.eventID))
      );
    });
    if (byStringId.length > 0) {
      const seen2 = new Set<string>();
      const unique2 = byStringId.filter((m) => {
        const key = `${m.eventID}_${m.type}`;
        if (seen2.has(key)) return false;
        seen2.add(key);
        return true;
      });
      return unique2.sort(
        (a, b) =>
          messages.findIndex((m) => m === a) -
          messages.findIndex((m) => m === b)
      );
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
      segment.ids.forEach(id => {
        ids.add(id);
      });
    });
    return ids;
  }, [segments]);

  // Get unsummarized messages (messages not included in any segment)
  const unsummarizedMessages = React.useMemo(() => {
    return messages.filter(msg => {
      return !msg.eventID || !summarizedIds.has(msg.eventID);
    });
  }, [messages, summarizedIds]);

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

      {/* Segments */}
      {segments.map((segment, idx) => (
        <div
          key={idx}
          className="border border-tertiary rounded-lg overflow-hidden"
        >
          <div
            className="bg-base-secondary p-3 flex justify-between items-center cursor-pointer hover:bg-tertiary transition-colors"
            onClick={() => toggleSegment(idx.toString())}
          >
            <div>
              <h3 className="font-medium text-content">{segment.title}</h3>
              <p className="text-sm text-tertiary-light">
                {segment.timestamp_range}
              </p>
            </div>
            <div className="text-tertiary-light">
              {expandedSegments[idx.toString()] ? (
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

          {expandedSegments[idx.toString()] && (
            <div className="p-3 bg-base">
              <div className="mb-3">
                <p className="text-content">{segment.summary}</p>
              </div>

              <div className="flex flex-col gap-2 mt-4">
                {(() => {
                  const segMsgs = getMessagesForSegment(
                    segment.ids,
                    idx,
                    segments.length,
                    segment
                  );
                  if (segMsgs.length === 0) {
                    return (
                      <div className="text-tertiary-light italic text-sm p-2">
                        No messages found for this segment.
                      </div>
                    );
                  }
                  return segMsgs.map((msg, mi) => {
                    const showConfirm =
                      messages.length - 1 === mi &&
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

      {/* Display unsummarized messages */}
      {unsummarizedMessages.length > 0 && (
        <div className="flex flex-col gap-2">
          {unsummarizedMessages.map((msg, idx) => {
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
