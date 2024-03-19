// App.tsx
import React, { useState } from "react";
import "./App.css";
import ChatInterface from "./components/ChatInterface";
import Terminal from "./components/Terminal";
import Planner from "./components/Planner";
import CodeEditor from "./components/CodeEditor";
import Browser from "./components/Browser";

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

function App(): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabOption>("terminal");
  // URL of browser window (placeholder for now, will be replaced with the actual URL later)
  const [url] = useState("https://github.com/OpenDevin/OpenDevin");
  // Base64-encoded screenshot of browser window (placeholder for now, will be replaced with the actual screenshot later)
  const [screenshotSrc] = useState(
    "data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mN0uGvyHwAFCAJS091fQwAAAABJRU5ErkJggg==",
  );

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
    browser: {
      name: "Browser",
      component: <Browser url={url} screenshotSrc={screenshotSrc} />,
    },
  };

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
