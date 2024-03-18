// App.tsx
import React, { useState } from "react";
import "./App.css";
import ChatInterface from "./components/ChatInterface";
import Terminal from "./components/Terminal";
import Planner from "./components/Planner";
import CodeEditor from "./components/CodeEditor";

const TAB_OPTIONS = ["terminal", "planner", "code"] as const;
type TabOption = (typeof TAB_OPTIONS)[number];

const tabData = {
  terminal: {
    name: "Terminal",
    component: <Terminal />,
  },
  planner: {
    name: "Planner",
    component: <Planner />,
  },
  code: {
    name: "Code Editor",
    component: <CodeEditor />,
  },
};

type TabProps = {
  name: string;
  active: boolean;
  onClick: () => void;
};
function Tab({ name, active, onClick }: TabProps): JSX.Element {
  return (
    <div className={`tab ${active ? "active" : ""}`} onClick={() => onClick()}>
      {name}
    </div>
  );
}

function App(): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabOption>("terminal");

  return (
    <div className="app">
      <div className="left-pane">
        <ChatInterface />
      </div>
      <div className="right-pane">
        <div className="tab-container">
          {TAB_OPTIONS.map((tab) => (
            <Tab
              key={tab}
              name={tabData[tab].name}
              active={activeTab === tab}
              onClick={() => setActiveTab(tab)}
            />
          ))}
        </div>
        <div className="tab-content">{tabData[activeTab].component}</div>
      </div>
    </div>
  );
}

export default App;
