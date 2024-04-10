import { Tab, Tabs } from "@nextui-org/react";
import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { FaCode } from "react-icons/fa6";
import { IoIosGlobe } from "react-icons/io";
import Calendar from "../assets/calendar";
import { I18nKey } from "../i18n/declaration";
import { AllTabs, TabOption, TabType } from "../types/TabOption";
import Browser from "./Browser";
import CodeEditor from "./CodeEditor";
import Planner from "./Planner";

function Workspace() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabType>(TabOption.CODE);

  const tabData = useMemo(
    () => ({
      [TabOption.PLANNER]: {
        name: t(I18nKey.WORKSPACE$PLANNER_TAB_LABEL),
        icon: <Calendar />,
        component: <Planner key="planner" />,
      },
      [TabOption.CODE]: {
        name: t(I18nKey.WORKSPACE$CODE_EDITOR_TAB_LABEL),
        icon: <FaCode size={18} />,
        component: <CodeEditor key="code" />,
      },
      [TabOption.BROWSER]: {
        name: t(I18nKey.WORKSPACE$BROWSER_TAB_LABEL),
        icon: <IoIosGlobe size={18} />,
        component: <Browser key="browser" />,
      },
    }),
    [t],
  );

  return (
    <>
      <div
        role="tablist"
        className="tabs tabs-bordered tabs-lg border-b border-neutral-600"
      >
        <Tabs
          disableCursorAnimation
          classNames={{
            tabList:
              "w-full relative rounded-none bg-neutral-800 p-0 border-divider gap-0 h-[36px]",
            cursor: "w-full bg-neutral-800  rounded-none",
            tab: " rounded-none border-neutral-600 border-r-[1px] border-r",
            tabContent: "group-data-[selected=true]:text-neutral-50",
          }}
          variant="light"
          size="lg"
          onSelectionChange={(v) => {
            setActiveTab(v as TabType);
          }}
        >
          {AllTabs.map((tab) => (
            <Tab
              key={tab}
              title={
                <div className="flex items-center space-x-2 justify-center text-xs">
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
          className="h-full w-full bg-neutral-800"
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
