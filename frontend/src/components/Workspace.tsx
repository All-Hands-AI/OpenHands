import React, { useMemo, useState } from "react";
import { Tab, Tabs } from "@nextui-org/react";
import { useTranslation } from "react-i18next";
import Terminal from "./Terminal";
import Planner from "./Planner";
import CodeEditor from "./CodeEditor";
import Browser from "./Browser";
import { TabType, TabOption, AllTabs } from "../types/TabOption";
import CmdLine from "../assets/cmd-line";
import Calendar from "../assets/calendar";
import Earth from "../assets/earth";
import Pencil from "../assets/pencil";
import { I18nKey } from "../i18n/declaration";

function Workspace() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabType>(TabOption.TERMINAL);

  const tabData = useMemo(
    () => ({
      [TabOption.TERMINAL]: {
        name: t(I18nKey.WORKSPACE$TERMINAL_TAB_LABEL),
        icon: <CmdLine />,
        component: <Terminal key="terminal" />,
      },
      [TabOption.PLANNER]: {
        name: t(I18nKey.WORKSPACE$PLANNER_TAB_LABEL),
        icon: <Calendar />,
        component: <Planner key="planner" />,
      },
      [TabOption.CODE]: {
        name: t(I18nKey.WORKSPACE$CODE_EDITOR_TAB_LABEL),
        icon: <Pencil />,
        component: <CodeEditor key="code" />,
      },
      [TabOption.BROWSER]: {
        name: t(I18nKey.WORKSPACE$BROWSER_TAB_LABEL),
        icon: <Earth />,
        component: <Browser key="browser" />,
      },
    }),
    [t],
  );

  return (
    <>
      <div className="w-full p-4 text-2xl font-bold select-none">
        {t(I18nKey.WORKSPACE$TITLE)}
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
