// App.tsx
import React, { useState } from "react";
import "./App.css";
import ChatInterface from "./components/ChatInterface";
import Terminal from "./components/Terminal";
import Planner from "./components/Planner";
import CodeEditor from "./components/CodeEditor";
import Browser from "./components/Browser";
import Errors from "./components/Errors";

const TAB_OPTIONS = ["terminal", "planner", "code", "browser"] as const;
type TabOption = (typeof TAB_OPTIONS)[number];

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

const tabData = {
  terminal: {
    name: "Terminal",
    component: null,
  },
  planner: {
    name: "Planner",
    component: <Planner key="planner" />,
  },
  code: {
    name: "Code Editor",
    component: <CodeEditor key="code" />,
  },
  browser: {
    name: "Browser",
    component: <Browser key="browser" />,
  },
};

function App(): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabOption>("terminal");

  return (
    <div className="app">
      <Errors />
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
        {/* Keep terminal permanently open - see component for more details */}
        <Terminal key="terminal" hidden={activeTab !== "terminal"} />
        <div className="tab-content">{tabData[activeTab].component}</div>
      </div>
    </div>
  );
}

export default App;
