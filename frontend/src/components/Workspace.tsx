import React, { useState } from "react";
import Terminal from "./Terminal";
import Planner from "./Planner";
import CodeEditor from "./CodeEditor";
import Browser from "./Browser";
import { TabType, TabOption, AllTabs } from "../types/TabOption";

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
    component: <Terminal key="terminal" />,
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

function Workspace() {
  const [activeTab, setActiveTab] = useState<TabType>(TabOption.TERMINAL);

  return (
    <>
      <div className="w-full p-4 text-2xl font-bold select-none">
        OpenDevin Workspace
      </div>
      <div role="tablist" className="tabs tabs-bordered tabs-lg ">
        {AllTabs.map((tab) => (
          <Tab
            key={tab}
            name={tabData[tab].name}
            active={activeTab === tab}
            onClick={() => setActiveTab(tab)}
          />
        ))}
      </div>
      <div className="h-full w-full p-4 bg-bg-workspace">
        {tabData[activeTab].component}
      </div>
    </>
  );
}
export default Workspace;
