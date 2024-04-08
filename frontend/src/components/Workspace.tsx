import { Tab, Tabs } from "@nextui-org/react";
import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { IoIosGlobe } from "react-icons/io";
import { VscCode } from "react-icons/vsc";
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
        icon: <VscCode size={18} />,
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
        className="tabs tabs-bordered tabs-lg border-b border-neutral-600 flex"
      >
        <Tabs
          disableCursorAnimation
          classNames={{
            base: "w-full",
            tabList:
              "w-full relative rounded-none bg-neutral-900 p-0 gap-0 h-[36px] flex",
            tab: "rounded-none border-neutral-600 data-[selected=true]:bg-neutral-800",
            tabContent: "group-data-[selected=true]:text-neutral-50",
          }}
          size="lg"
          onSelectionChange={(v) => {
            setActiveTab(v as TabType);
          }}
        >
          {AllTabs.map((tab, index) => (
            <Tab
              key={tab}
              className={`flex-grow ${index + 1 === AllTabs.length ? "" : "border-r"}`}
              title={
                <div className="flex grow items-center gap-2 justify-center text-xs">
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
