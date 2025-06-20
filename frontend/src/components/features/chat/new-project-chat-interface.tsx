import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { useIsAuthed } from "#/hooks/query/use-is-authed";
import { Paperclip, Send, Pause, MessageSquare, Code, Loader, Layers } from "lucide-react";
import { LoadingScreen, TabbedInterface, CodeViewer, ThreadSimulator } from "./interface-components";

// Interface view types
type InterfaceView = 'main' | 'loading' | 'tabbed' | 'code' | 'thread';

export function NewProjectChatInterface() {
  console.log("🔍 [DEBUG] NewProjectChatInterface component starting...");

  const { t } = useTranslation();
  const { data: isAuthed } = useIsAuthed();
  const [input, setInput] = React.useState("");
  const [currentView, setCurrentView] = React.useState<InterfaceView>('main');

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    setInput(e.target.value);
  }

  function handleSend() {
    if (input.trim()) {
      // TODO: send message logic here
      console.log("Send:", input);
      setInput("");
    }
  }

  function handleInputKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      handleSend();
    }
  }

  function handleViewChange(view: InterfaceView) {
    setCurrentView(view);
  }

  console.log("🔍 [DEBUG] NewProjectChatInterface - Auth status:", isAuthed);

  // Render the main canvas content based on current view
  function renderCanvasContent() {
    if (currentView === 'loading') {
      return <LoadingScreen onBack={() => handleViewChange('main')} />;
    }

    if (currentView === 'thread') {
      return <ThreadSimulator onBack={() => handleViewChange('main')} />;
    }

    // Default main view
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <h2 className="text-xl font-semibold text-content mb-4">
            Project Interface
          </h2>
          <p className="text-sm text-content-secondary mb-6">
            This is the experimental project interface canvas.
            Click on the interface types below to explore different designs.
          </p>

          <div className="space-y-3">
            <div className="bg-base-secondary rounded-lg p-4 border border-border">
              <h3 className="font-medium text-content mb-2">Quick Start</h3>
              <p className="text-xs text-content-secondary">
                Start with a simple prompt or choose from templates
              </p>
            </div>

            <div className="bg-base-secondary rounded-lg p-4 border border-border">
              <h3 className="font-medium text-content mb-2">Import Project</h3>
              <p className="text-xs text-content-secondary">
                Connect to existing repositories or upload code
              </p>
            </div>

            <div className="bg-base-secondary rounded-lg p-4 border border-border">
              <h3 className="font-medium text-content mb-2">Templates</h3>
              <p className="text-xs text-content-secondary">
                Choose from pre-built project templates
              </p>
            </div>

            {/* Interface Simulator Buttons - now in the main canvas */}
            <div className="bg-base-secondary rounded-lg p-4 border border-border">
              <h3 className="font-medium text-content mb-3">Interface Simulator</h3>
              <p className="text-xs text-content-secondary mb-4">
                Explore different interface designs and components
              </p>
              <div className="grid grid-cols-1 gap-2">
                <button
                  onClick={() => handleViewChange('thread')}
                  className="flex items-center justify-center gap-2 bg-primary text-black rounded-lg px-4 py-3 text-sm font-medium hover:bg-primary/90 transition-colors"
                >
                  <MessageSquare className="w-4 h-4" />
                  AI Thread Simulator
                </button>
                <button
                  onClick={() => handleViewChange('loading')}
                  className="flex items-center justify-center gap-2 bg-base rounded-lg px-4 py-3 text-sm font-medium border border-border hover:bg-base-tertiary transition-colors"
                >
                  <Loader className="w-4 h-4" />
                  Loading Screen
                </button>
                <button
                  onClick={() => handleViewChange('loading')}
                  className="flex items-center justify-center gap-2 bg-base rounded-lg px-4 py-3 text-sm font-medium border border-border hover:bg-base-tertiary transition-colors"
                >
                  <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                  Loading Button
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  console.log("🔍 [DEBUG] NewProjectChatInterface - Rendering main interface");

  return (
    <div className="h-full flex flex-col justify-between">
      {/* Canvas content - changes based on current view */}
      {renderCanvasContent()}

      {/* Chat input area - always visible at bottom */}
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

      {/* GIT CONTROLS - always visible at bottom */}
      <div className="flex flex-wrap gap-2 px-4 pb-4">
        <button className="flex items-center gap-1 bg-base-secondary rounded-full px-4 py-1.5 text-content font-medium text-xs focus:outline-none">
          {/* Lucide GitBranch icon */}
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M6 3v12"/><circle cx="6" cy="18" r="3"/><circle cx="6" cy="3" r="3"/><circle cx="18" cy="6" r="3"/><path d="M6 6h12"/></svg>
          My Project
          <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
        </button>
        <button className="flex items-center gap-1 bg-base-secondary rounded-full px-4 py-1.5 text-content font-medium text-xs focus:outline-none">
          {/* Lucide GitBranch icon */}
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M6 3v12"/><circle cx="6" cy="18" r="3"/><circle cx="6" cy="3" r="3"/><circle cx="18" cy="6" r="3"/><path d="M6 6h12"/></svg>
          main
          <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
        </button>
        <button className="flex items-center gap-1 bg-base-secondary rounded-full px-4 py-1.5 text-content font-medium text-xs focus:outline-none">
          {/* Lucide Upload icon */}
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M12 19V6M5 12l7-7 7 7"/></svg>
          Push
        </button>
        <button className="flex items-center gap-1 bg-base-secondary rounded-full px-4 py-1.5 text-content font-medium text-xs focus:outline-none">
          {/* Lucide Download icon */}
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M12 5v13M19 12l-7 7-7-7"/></svg>
          Pull
        </button>
        <button className="flex items-center gap-1 bg-base-secondary rounded-full px-4 py-1.5 text-content font-medium text-xs focus:outline-none">
          {/* Lucide GitPullRequest icon */}
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M6 9v6m6-3h6"/></svg>
          Create PR
        </button>
      </div>
    </div>
  );
}
