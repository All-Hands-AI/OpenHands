import React, { useState } from "react";
import "./App.css";
import { useSelector } from "react-redux";
import ChatInterface from "./components/ChatInterface";
import Terminal from "./components/Terminal";
import Planner from "./components/Planner";
import CodeEditor from "./components/CodeEditor";
import Browser from "./components/Browser";
import Errors from "./components/Errors";
import BannerSettings from "./components/BannerSettings";
import { RootState } from "./store";
import assistantAvatar from "./assets/assistant-avatar.png";

const TAB_OPTIONS = ["terminal", "planner", "code", "browser"] as const;
type TabOption = (typeof TAB_OPTIONS)[number];

type TabProps = {
  name: string;
  active: boolean;
  onClick: () => void;
};
function Tab({ name, active, onClick }: TabProps): JSX.Element {
  return (
    <div
      className={`tab ${active ? "tab-active" : ""}`}
      onClick={() => onClick()}
    >
      <p className="font-bold">{name}</p>
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

function InitializingStatus(): JSX.Element {
  return (
    <div className="initializing-status">
      <img src={assistantAvatar} alt="assistant avatar" className="avatar" />
      <div>Initializing agent (may take up to 10 seconds)...</div>
    </div>
  );
}

function App(): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabOption>("terminal");
  const { initialized } = useSelector((state: RootState) => state.task);

  return (
    <div className="app flex">
      <Errors />
      {initialized ? (
        <>
          <div className="left-pane">
            <ChatInterface />
          </div>
          <div className="right-pane">
            <div className="navbar bg-base-100">
              <div className="flex-1">
                <div className="btn btn-ghost text-xl xl:w-full xl:h-full h-1/2 w-1/2 ml-4">
                  OpenDevin Workspace
                </div>
              </div>
              <div className="flex">
                <BannerSettings />
              </div>
            </div>
            <div
              role="tablist"
              className="tabs tabs-bordered tabs-lg bg-base-100"
            >
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
            {tabData[activeTab].component}
          </div>
        </>
      ) : (
        <InitializingStatus />
      )}
    </div>
  );
}

export default App;
