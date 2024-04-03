import React, { useState } from "react";
import { Tab, Tabs } from "@nextui-org/react";
import Terminal from "./Terminal";
import Planner from "./Planner";
import CodeEditor from "./CodeEditor";
import Browser from "./Browser";
import { TabType, TabOption, AllTabs } from "../types/TabOption";
import CmdLine from "../assets/cmd-line";
import Calendar from "../assets/calendar";
import Earth from "../assets/earth";
import Pencil from "../assets/pencil";

const tabData = {
  [TabOption.TERMINAL]: {
    name: "Terminal",
    icon: <CmdLine />,
    component: <Terminal key="terminal" />,
  },
  [TabOption.PLANNER]: {
    name: "Planner",
    icon: <Calendar />,
    component: <Planner key="planner" />,
  },
  [TabOption.CODE]: {
    name: "Code Editor",
    icon: <Pencil />,
    component: <CodeEditor key="code" />,
  },
  [TabOption.BROWSER]: {
    name: "Browser",
    icon: <Earth />,
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
        <Tabs
          variant="underlined"
          size="lg"
          onSelectionChange={(v) => {
            setActiveTab(v as TabType);
          }}
        >
          {AllTabs.map((tab) => (
            <Tab
              key={tab}
              title={
                <div className="flex items-center space-x-2">
                  {tabData[tab].icon}
                  <span>{tabData[tab].name}</span>
                </div>
              }
            />
          ))}
        </Tabs>
      </div>
      {Object.keys(tabData).map((tab) => (
        <div
          className="h-full w-full p-4 bg-bg-workspace"
          key={tab}
          hidden={activeTab !== tab}
        >
          {tabData[tab as TabType].component}
        </div>
      ))}
    </>
  );
}
export default Workspace;
