import React from "react";
import ChatMessage from "./ChatMessage";
import { MdContentCopy } from 'react-icons/md';

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text);
    console.log('Message copied to clipboard');
  } catch (err) {
    console.error('Failed to copy text: ', err);
  }
};

interface ChatProps {
  messages: Message[];
}

function Chat({ messages }: ChatProps) {
  const endOfMessagesRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col gap-3">
      {messages.map((message, index) => (
        <div key={index} className="flex justify-between items-center p-2 bg-white shadow rounded-lg">
          <ChatMessage message={message} />
          <button onClick={() => copyToClipboard(message.text)} className="ml-2 p-1 rounded hover:bg-gray-200 focus:outline-none" aria-label="Copy message">
            <MdContentCopy size={24} />
          </button>
        </div>
      ))}
      <div ref={endOfMessagesRef} />
    </div>
  );
}

export default Chat;
