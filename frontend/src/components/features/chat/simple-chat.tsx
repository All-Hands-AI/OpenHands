/* eslint-disable i18next/no-literal-string */
import React from "react";
import { io, Socket } from "socket.io-client";
import OpenHands from "#/api/open-hands";
import { BrandButton } from "#/components/features/settings/brand-button";

interface SimpleChatProps {
  conversationId: string;
}

interface ChatEvent {
  id?: number;
  type?: string;
  content?: string;
  [key: string]: unknown;
}

export function SimpleChat({ conversationId }: SimpleChatProps) {
  const [events, setEvents] = React.useState<ChatEvent[]>([]);
  const [input, setInput] = React.useState("");

  React.useEffect(() => {
    const s: Socket = io("/", {
      path: "/socket.io",
      query: {
        conversation_id: conversationId,
        latest_event_id: -1,
      },
      transports: ["websocket"],
    });

    s.on("oh_event", (evt: ChatEvent) => {
      setEvents((prev) => [...prev, evt]);
    });

    return () => {
      s.disconnect();
    };
  }, [conversationId]);

  const send = async () => {
    if (!input.trim()) return;
    await OpenHands.sendCommand(conversationId, {
      role: "user",
      type: "message",
      content: input,
    });
    setInput("");
  };

  return (
    <div className="flex flex-col h-full border border-tertiary rounded">
      <div className="flex-1 overflow-auto p-3 text-sm">
        {events.map((e, idx) => (
          <div key={idx} className="mb-2">
            <div className="opacity-60 text-xs">{e.type || "event"}</div>
            <pre className="whitespace-pre-wrap break-words">
              {e.content || JSON.stringify(e)}
            </pre>
          </div>
        ))}
      </div>
      <div className="border-t border-tertiary p-2 flex gap-2 items-center">
        <input
          className="flex-1 bg-tertiary border border-tertiary-alt rounded px-2 py-1"
          placeholder="Type a command or message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <BrandButton variant="primary" type="button" onClick={send}>
          Send
        </BrandButton>
      </div>
    </div>
  );
}
