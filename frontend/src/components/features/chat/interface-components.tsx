import React from "react";
import { ArrowLeft, MessageSquare, Code, FileText, Settings, Users, GitBranch, Play, Pause, RotateCcw } from "lucide-react";
import { TypingIndicator } from "./typing-indicator";
import { ErrorMessage } from "./error-message";
import { Suggestions } from "../suggestions/suggestions";
import { Suggestion } from "../suggestions/suggestion-item";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface BackButtonProps {
  onBack: () => void;
}

function BackButton({ onBack }: BackButtonProps) {
  return (
    <button
      onClick={onBack}
      className="flex items-center gap-2 text-content-secondary hover:text-content transition-colors mb-4"
    >
      <ArrowLeft className="w-4 h-4" />
      Back to Interface
    </button>
  );
}

function GeneratingStopRow() {
  return (
    <div className="flex items-center gap-4 mt-2 mb-4">
      <span className="text-content-secondary text-sm">Generating</span>
      <button className="text-content-secondary text-sm flex items-center gap-1 hover:text-content transition-colors">
        Stop
        <span className="ml-1 text-xs">⇧⌘⏎</span>
      </button>
    </div>
  );
}

export function LoadingScreen({ onBack }: BackButtonProps) {
  return (
    <div className="flex-1 flex flex-col">
      <BackButton onBack={onBack} />

      <div className="flex-1 flex flex-col justify-center items-center p-8 rounded-xl">
        <div className="text-center max-w-md">
          <div className="mb-6">
            <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-content mb-2">Initializing Project</h2>
            <p className="text-sm text-content-secondary">
              Setting up your development environment...
            </p>
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-base rounded-lg">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-content">Environment setup</span>
            </div>
            <div className="flex items-center gap-3 p-3 bg-base rounded-lg">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-content">Dependencies installed</span>
            </div>
            <div className="flex items-center gap-3 p-3 bg-base rounded-lg">
              <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-content">Starting development server...</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function TabbedInterface({ onBack }: BackButtonProps) {
  const [activeTab, setActiveTab] = React.useState('chat');

  const tabs = [
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'code', label: 'Code', icon: Code },
    { id: 'files', label: 'Files', icon: FileText },
    { id: 'settings', label: 'Settings', icon: Settings },
    { id: 'team', label: 'Team', icon: Users },
  ];

  return (
    <div className="h-full flex flex-col">
      <BackButton onBack={onBack} />

      <div className="flex-1 flex flex-col bg-base-secondary rounded-xl">
        {/* Tab Navigation */}
        <div className="flex border-b border-border">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'text-primary border-b-2 border-primary'
                    : 'text-content-secondary hover:text-content'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <div className="flex-1 p-4">
          {activeTab === 'chat' && (
            <div className="bg-base rounded-lg p-4 h-full">
              <h3 className="font-medium text-content mb-3">Chat Interface</h3>
              <div className="space-y-3">
                <div className="flex gap-3">
                  <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-black text-sm font-medium">U</div>
                  <div className="flex-1">
                    <p className="text-sm text-content">Can you help me with this component?</p>
                    <p className="text-xs text-content-secondary mt-1">2:30 PM</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="w-8 h-8 bg-base-tertiary rounded-full flex items-center justify-center text-content text-sm font-medium">AI</div>
                  <div className="flex-1">
                    <p className="text-sm text-content">Of course! I'd be happy to help you with that component.</p>
                    <p className="text-xs text-content-secondary mt-1">2:31 PM</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'code' && (
            <div className="bg-base rounded-lg p-4 h-full">
              <h3 className="font-medium text-content mb-3">Code Editor</h3>
              <div className="bg-base-tertiary rounded-lg p-3 font-mono text-sm text-content">
                <div className="text-content-secondary">// React Component</div>
                <div className="text-blue-400">function</div> <div className="text-yellow-400">MyComponent</div>() {'{'}<br/>
                <div className="text-blue-400 ml-4">return</div> (<br/>
                <div className="ml-4">&lt;<div className="text-green-400">div</div>&gt;</div><br/>
                <div className="ml-8 text-content">Hello World!</div><br/>
                <div className="ml-4">&lt;/<div className="text-green-400">div</div>&gt;</div><br/>
                <div>);</div>
                {'}'}
              </div>
            </div>
          )}

          {activeTab === 'files' && (
            <div className="bg-base rounded-lg p-4 h-full">
              <h3 className="font-medium text-content mb-3">File Explorer</h3>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-content">
                  <FileText className="w-4 h-4" />
                  src/
                </div>
                <div className="flex items-center gap-2 text-sm text-content ml-4">
                  <FileText className="w-4 h-4" />
                  components/
                </div>
                <div className="flex items-center gap-2 text-sm text-content ml-8">
                  <FileText className="w-4 h-4" />
                  App.tsx
                </div>
                <div className="flex items-center gap-2 text-sm text-content ml-8">
                  <FileText className="w-4 h-4" />
                  index.tsx
                </div>
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="bg-base rounded-lg p-4 h-full">
              <h3 className="font-medium text-content mb-3">Settings</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-content">Dark Mode</span>
                  <div className="w-10 h-6 bg-primary rounded-full relative">
                    <div className="w-4 h-4 bg-black rounded-full absolute top-1 right-1"></div>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-content">Notifications</span>
                  <div className="w-10 h-6 bg-base-tertiary rounded-full relative">
                    <div className="w-4 h-4 bg-content-secondary rounded-full absolute top-1 left-1"></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'team' && (
            <div className="bg-base rounded-lg p-4 h-full">
              <h3 className="font-medium text-content mb-3">Team Members</h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-black text-sm font-medium">JD</div>
                  <div>
                    <p className="text-sm font-medium text-content">John Doe</p>
                    <p className="text-xs text-content-secondary">Frontend Developer</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-base-tertiary rounded-full flex items-center justify-center text-content text-sm font-medium">JS</div>
                  <div>
                    <p className="text-sm font-medium text-content">Jane Smith</p>
                    <p className="text-xs text-content-secondary">Backend Developer</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function CodeViewer({ onBack }: BackButtonProps) {
  return (
    <div className="h-full flex flex-col">
      <BackButton onBack={onBack} />

      <div className="flex-1 flex flex-col bg-base-secondary rounded-xl">
        {/* Code Header */}
        <div className="flex items-center justify-between p-4 bg-base rounded-t-xl border-b border-border">
          <div className="flex items-center gap-2">
            <Code className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-content">App.tsx</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-xs text-content-secondary">Saved</span>
          </div>
        </div>

        {/* Code Content */}
        <div className="flex-1 p-4">
          <div className="bg-base rounded-lg p-4 h-full font-mono text-sm">
            <div className="text-content-secondary mb-4">// React Application Entry Point</div>

            <div className="text-blue-400">import</div> <div className="text-yellow-400">React</div> <div className="text-blue-400">from</div> <div className="text-green-400">'react'</div>;<br/>
            <div className="text-blue-400">import</div> <div className="text-yellow-400">ReactDOM</div> <div className="text-blue-400">from</div> <div className="text-green-400">'react-dom/client'</div>;<br/>
            <div className="text-blue-400">import</div> <div className="text-yellow-400">App</div> <div className="text-blue-400">from</div> <div className="text-green-400">'./App'</div>;<br/><br/>

            <div className="text-blue-400">const</div> <div className="text-yellow-400">root</div> = <div className="text-yellow-400">ReactDOM</div>.<div className="text-blue-400">createRoot</div>(<br/>
            <div className="ml-4 text-yellow-400">document</div>.<div className="text-blue-400">getElementById</div>(<div className="text-green-400">'root'</div>)<br/>
            <div>);</div><br/><br/>

            <div className="text-yellow-400">root</div>.<div className="text-blue-400">render</div>(<br/>
            <div className="ml-4">&lt;<div className="text-green-400">React.StrictMode</div>&gt;</div><br/>
            <div className="ml-8">&lt;<div className="text-green-400">App</div> /&gt;</div><br/>
            <div className="ml-4">&lt;/<div className="text-green-400">React.StrictMode</div>&gt;</div><br/>
            <div>);</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function SimulatedChatMessage({ type, message }: { type: 'user' | 'agent'; message: string }) {
  return (
    <div className={`flex ${type === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`rounded-xl p-4 text-sm max-w-2xl w-fit shadow ${
          type === 'user'
            ? 'bg-base-tertiary text-content self-end'
            : 'bg-base text-content self-start'
        }`}
      >
        <Markdown remarkPlugins={[remarkGfm]}>{message}</Markdown>
      </div>
    </div>
  );
}

// Add a taxonomy for system/status messages
const STATUS_TYPES = [
  'info', 'success', 'warning', 'error', 'progress', 'action-required', 'pending', 'complete',
] as const;
type StatusType = typeof STATUS_TYPES[number];

function SimulatedStatusMessage({ type, message }: { type: StatusType; message: string }) {
  let base = 'text-xs rounded-full px-4 py-1 my-2 font-medium inline-block ';
  let style = '';
  switch (type) {
    case 'info':
      style = 'bg-tertiary text-content-secondary';
      break;
    case 'success':
      style = 'bg-green-600/20 text-green-500';
      break;
    case 'warning':
      style = 'bg-yellow-600/20 text-yellow-500';
      break;
    case 'error':
      style = 'bg-red-600/20 text-red-500';
      break;
    case 'progress':
      style = 'bg-blue-600/20 text-blue-400';
      break;
    case 'action-required':
      style = 'bg-primary/10 text-primary border border-primary';
      break;
    case 'pending':
      style = 'bg-base-tertiary text-content-secondary italic';
      break;
    case 'complete':
      style = 'bg-green-700/20 text-green-600';
      break;
    default:
      style = 'bg-tertiary text-content-secondary';
  }
  return (
    <div className="flex justify-center">
      <span className={base + style}>{message}</span>
    </div>
  );
}

function SimulatedSuggestions({ suggestions }: { suggestions: string[] }) {
  return (
    <div className="flex flex-wrap gap-2 py-2">
      {suggestions.map((s, i) => (
        <button key={i} className="border border-border rounded-xl px-4 py-2 text-sm font-medium bg-base hover:bg-tertiary transition-colors">
          {s}
        </button>
      ))}
    </div>
  );
}

function SimulatedActionSuggestions({ actions }: { actions: string[] }) {
  return (
    <div className="flex gap-2 py-2">
      {actions.map((a, i) => (
        <button key={i} className="px-3 py-1.5 rounded-full bg-base-secondary border border-border text-xs font-medium hover:bg-base-tertiary transition-colors">
          {a}
        </button>
      ))}
    </div>
  );
}

export function ThreadSimulator({ onBack }: BackButtonProps) {
  // Simulated conversation
  const messages = [
    { id: 1, type: 'user', content: 'Can you help me create a React component with **markdown** and `inline code`?', timestamp: '2:30 PM' },
    { id: 2, type: 'agent', content: 'Of course! Here is a simple example:\n\n```jsx\nfunction MyButton() {\n  return <button>Click me</button>;\n}\n```', timestamp: '2:31 PM' },
    { id: 3, type: 'user', content: 'How do I add a loading spinner?', timestamp: '2:32 PM' },
    { id: 4, type: 'agent', content: 'You can use a CSS spinner or a library like `react-spinners`.\n\nWould you like a code example?', timestamp: '2:33 PM' },
  ];
  const suggestions = ['Add a loading spinner', 'Show error message', 'Show typing indicator', 'Show suggestions'];
  const actions = ['Approve', 'Reject', 'Retry'];

  // Example system/status messages
  const statusMessages = [
    { type: 'info', message: 'Agent is thinking...' },
    { type: 'success', message: 'Component created successfully.' },
    { type: 'warning', message: 'This will overwrite your changes.' },
    { type: 'error', message: 'Failed to connect to server.' },
    { type: 'progress', message: 'Uploading file (45%)...' },
    { type: 'action-required', message: 'Please review and accept the changes.' },
    { type: 'pending', message: 'Waiting for user input...' },
    { type: 'complete', message: 'All tasks completed.' },
  ] as { type: StatusType; message: string }[];

  return (
    <div className="flex-1 flex flex-col">
      <BackButton onBack={onBack} />
      <div className="flex-1 flex flex-col max-w-2xl w-full mx-auto px-4 pt-4 pb-2 gap-2">
        {/* Simulated chat bubbles */}
        {messages.map((msg, idx) => (
          <React.Fragment key={msg.id}>
            <SimulatedChatMessage type={msg.type as 'user' | 'agent'} message={msg.content} />
            {/* Add Generating/Stop row after user message only */}
            {msg.type === 'user' && idx === 0 && <GeneratingStopRow />}
          </React.Fragment>
        ))}
        {/* Simulated system/status messages */}
        {statusMessages.map((s, i) => (
          <SimulatedStatusMessage key={i} type={s.type} message={s.message} />
        ))}
        {/* Simulated typing indicator */}
        <div className="flex justify-start"><TypingIndicator /></div>
        {/* Simulated error message */}
        <ErrorMessage defaultMessage={"Something went wrong. Please try again."} />
        {/* Simulated suggestions */}
        <SimulatedSuggestions suggestions={suggestions} />
        {/* Simulated action suggestions */}
        <SimulatedActionSuggestions actions={actions} />
      </div>
    </div>
  );
}
