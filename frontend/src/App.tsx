// App.tsx
import React, { useState } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import Terminal from './components/Terminal';
import Planner from './components/Planner';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'terminal' | 'planner'>('terminal');

  return (
    <div className="app">
      <div className="left-pane">
        <ChatInterface />
      </div>
      <div className="right-pane">
        <div className="tab-container">
          <div
            className={`tab ${activeTab === 'terminal' ? 'active' : ''}`}
            onClick={() => setActiveTab('terminal')}
          >
            Shell
          </div>
          <div
            className={`tab ${activeTab === 'planner' ? 'active' : ''}`}
            onClick={() => setActiveTab('planner')}
          >
            Planner
          </div>
        </div>
        <div className="tab-content">
          {activeTab === 'terminal' ? <Terminal /> : <Planner />}
        </div>
      </div>
    </div>
  );
};

export default App;