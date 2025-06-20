/**
 * Chat Components Library
 *
 * This file contains the styles and components that were removed from the main interface
 * but are kept here for reference and potential future use.
 */

import React from "react";
import { MessageSquare, Pause, RotateCcw, Paperclip, Send } from "lucide-react";

/**
 * Thread Header Component Styles
 *
 * Removed from ThreadSimulator - this was the header with AI Assistant Thread title
 * and Pause/Reset buttons
 */
export function ThreadHeader() {
  return (
    <div className="flex items-center justify-between p-4 border-b border-border bg-base-secondary">
      <div className="flex items-center gap-3">
        <MessageSquare className="w-5 h-5 text-primary" />
        <div>
          <h3 className="text-sm font-medium text-content">AI Assistant Thread</h3>
          <p className="text-xs text-content-secondary">Real-time conversation</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button className="flex items-center gap-1 bg-base rounded-lg px-3 py-1.5 text-xs font-medium border border-border hover:bg-base-tertiary transition-colors">
          <Pause className="w-3 h-3" />
          Pause
        </button>
        <button className="flex items-center gap-1 bg-base rounded-lg px-3 py-1.5 text-xs font-medium border border-border hover:bg-base-tertiary transition-colors">
          <RotateCcw className="w-3 h-3" />
          Reset
        </button>
      </div>
    </div>
  );
}

/**
 * Chat Input Component Styles
 *
 * Removed from ThreadSimulator - this was the duplicate input area with
 * text input and send button
 */
export function ChatInput() {
  const [input, setInput] = React.useState('');

  const handleSend = () => {
    if (input.trim()) {
      console.log("Send:", input);
      setInput("");
    }
  };

  return (
    <div className="p-4 border-t border-border">
      <div className="flex items-center gap-3">
        <input
          type="text"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          className="flex-1 bg-base-secondary text-content placeholder-content-secondary outline-none rounded-lg px-3 py-2 text-sm"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim()}
          className="bg-primary text-black rounded-lg px-4 py-2 text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}

/**
 * Main Chat Interface Component Styles
 *
 * This is the main chat input area that remains in the interface
 * with attach file, input, send button, server status, and pause agent
 */
export function MainChatInput() {
  const [input, setInput] = React.useState("");

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    setInput(e.target.value);
  }

  function handleSend() {
    if (input.trim()) {
      console.log("Send:", input);
      setInput("");
    }
  }

  function handleInputKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      handleSend();
    }
  }

  return (
    <div className="px-4 pb-2">
      <div className="rounded-xl bg-base-secondary flex flex-col">
        <div className="flex items-center px-4 pt-3 pb-2">
          <button className="mr-3 text-content-secondary hover:text-content" aria-label="Attach file">
            <Paperclip className="w-4 h-4" />
          </button>
          <input
            type="text"
            placeholder="What do you want to build?"
            className="flex-1 bg-transparent text-content placeholder-content-secondary outline-none text-sm px-2"
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleInputKeyDown}
          />
          <button
            className="ml-3 bg-primary text-black rounded-full w-8 h-8 flex items-center justify-center hover:bg-primary/90 transition-colors"
            aria-label="Send"
            onClick={handleSend}
            disabled={!input.trim()}
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <div className="flex items-center justify-between px-4 pb-3">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-green-500 inline-block"></span>
            <span className="text-content text-xs">Server: Running</span>
          </div>
          <button className="flex items-center gap-1 bg-gray-200 rounded-full px-3 py-1 text-content font-medium text-xs focus:outline-none">
            <Pause className="w-4 h-4" />
            Pause Agent
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * CSS Classes Reference
 *
 * Key styling classes used in the chat components:
 *
 * Container:
 * - p-4 border-t border-border (input container)
 * - rounded-xl bg-base-secondary flex flex-col (main chat container)
 *
 * Input:
 * - flex-1 bg-base-secondary text-content placeholder-content-secondary outline-none rounded-lg px-3 py-2 text-sm
 * - flex-1 bg-transparent text-content placeholder-content-secondary outline-none text-sm px-2 (main input)
 *
 * Buttons:
 * - bg-primary text-black rounded-lg px-4 py-2 text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50
 * - bg-primary text-black rounded-full w-8 h-8 flex items-center justify-center hover:bg-primary/90 transition-colors (send button)
 * - bg-gray-200 rounded-full px-3 py-1 text-content font-medium text-xs focus:outline-none (pause agent)
 *
 * Header:
 * - flex items-center justify-between p-4 border-b border-border bg-base-secondary
 * - flex items-center gap-1 bg-base rounded-lg px-3 py-1.5 text-xs font-medium border border-border hover:bg-base-tertiary transition-colors
 */
