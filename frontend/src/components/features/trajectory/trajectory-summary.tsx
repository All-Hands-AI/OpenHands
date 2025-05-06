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
  // Keep previously fetched segments
  const [allSegments, setAllSegments] = React.useState<TrajectorySummarySegment[]>([]);

  // Append new segments only
  React.useEffect(() => {
    setAllSegments(prev => {
      const newOnes = segments.filter(s =>
        !prev.some(p => JSON.stringify(p.ids) === JSON.stringify(s.ids))
      );
      return newOnes.length > 0 ? [...prev, ...newOnes] : prev;
    });
  }, [segments]);

  // Track expanded/collapsed state per segment index
  const [expanded, setExpanded] = React.useState<Record<number, boolean>>({});
  React.useEffect(() => {
    const init: Record<number, boolean> = {};
    allSegments.forEach((_, i) => {
      init[i] = i === allSegments.length - 1;
    });
    setExpanded(init);
  }, [allSegments.length]);

  // Only exact ID matching
  const getMessagesForSegment = React.useCallback(
    (ids: number[]): Message[] => {
      if (!ids || ids.length === 0) return [];
      return messages
        .filter(m => m.eventID != null && ids.includes(m.eventID))
        .sort(
          (a, b) =>
            messages.findIndex(x => x === a) -
            messages.findIndex(x => x === b)
        );
    },
    [messages]
  );

  // Build content blocks in chronological order
  const contentBlocks = React.useMemo(() => {
    const blocks: React.ReactNode[] = [];
    const seen = new Set<number>();

    for (let idx = 0; idx < messages.length; idx++) {
      const msg = messages[idx];
      const segIdx = allSegments.findIndex(seg => seg.ids?.includes(msg.eventID!));

      if (segIdx >= 0) {
        // First time this segment appears
        if (!seen.has(segIdx)) {
          seen.add(segIdx);
          const segment = allSegments[segIdx];
          const segMsgs = getMessagesForSegment(segment.ids || []);

          blocks.push(
            <div
              key={`segment-${segIdx}`}
              className="border border-tertiary rounded-lg overflow-hidden mt-4"
            >
              <div
                className="bg-base-secondary p-3 flex justify-between items-center cursor-pointer hover:bg-tertiary transition-colors"
                onClick={() =>
                  setExpanded(prev => ({ ...prev, [segIdx]: !prev[segIdx] }))
                }
              >
                <div>
                  <h3 className="font-medium text-content">{segment.title}</h3>
                  <p className="text-sm text-tertiary-light">{segment.timestamp_range}</p>
                </div>
                <div className="text-tertiary-light">
                  {expanded[segIdx] ? (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
              </div>

              {expanded[segIdx] && (
                <div className="p-3 bg-base">
                  <p className="text-content mb-3">{segment.summary}</p>
                  <div className="flex flex-col gap-2">
                    {segMsgs.length === 0 ? (
                      <div className="text-tertiary-light italic text-sm p-2">
                        No messages in this segment.
                      </div>
                    ) : (
                      segMsgs.map((m, i) => {
                        const showConfirm =
                          i === segMsgs.length - 1 &&
                          m.sender === "assistant" &&
                          isAwaitingUserConfirmation;

                        if (m.type === "error" || m.type === "action") {
                          return (
                            <div key={i} className="text-content">
                              {m.thought && <ChatMessage type="assistant" message={m.thought} id={m.eventID} />}
                              <ExpandableMessage
                                type={m.type}
                                id={m.translationID}
                                message={m.content}
                                success={m.success}
                                eventID={m.eventID}
                              />
                              {showConfirm && <ConfirmationButtons />}
                            </div>
                          );
                        }

                        return (
                          <ChatMessage key={i} type={m.sender} message={m.content} id={m.eventID}>
                            {m.imageUrls && m.imageUrls.length > 0 && <ImageCarousel size="small" images={m.imageUrls} />}
                            {showConfirm && <ConfirmationButtons />}
                          </ChatMessage>
                        );
                      })
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        }
        // Skip individual messages part of a rendered segment
        continue;
      }

      // Regular, unsummarized messages
      const showConfirm =
        idx === messages.length - 1 &&
        msg.sender === "assistant" &&
        isAwaitingUserConfirmation;

      if (msg.type === "error" || msg.type === "action") {
        blocks.push(
          <div key={`msg-${idx}`} className="text-content mt-2">
            {msg.thought && <ChatMessage type="assistant" message={msg.thought} id={msg.eventID} />}
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
      } else {
        blocks.push(
          <ChatMessage key={`msg-${idx}`} type={msg.sender} message={msg.content} id={msg.eventID}>
            {msg.imageUrls && msg.imageUrls.length > 0 && <ImageCarousel size="small" images={msg.imageUrls} />}
            {showConfirm && <ConfirmationButtons />}
          </ChatMessage>
        );
      }
    }

    return blocks;
  }, [messages, allSegments, expanded, isAwaitingUserConfirmation, getMessagesForSegment]);

  return (
    <div className="flex flex-col gap-2 w-full">
      {allSegments.length > 0 && (
        <div className="bg-base-secondary p-4 rounded-lg border border-tertiary">
          <h2 className="text-lg font-semibold mb-2 text-content">Conversation Summary</h2>
          <p className="text-content">{overallSummary}</p>
        </div>
      )}
      {contentBlocks}
    </div>
  );
}
