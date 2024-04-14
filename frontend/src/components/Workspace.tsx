import { Tab, Tabs } from "@nextui-org/react";
import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { IoIosGlobe } from "react-icons/io";
import i18next from "i18next";
import Calendar from "../assets/calendar";
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
        name: i18next.t("WORKSPACE$PLANNER_TAB_LABEL"),
        icon: <Calendar />,
        component: <Planner key="planner" />,
      },
      [TabOption.CODE]: {
        name: i18next.t("WORKSPACE$CODE_EDITOR_TAB_LABEL"),
        icon: <FaCode size={18} />,
        component: <CodeEditor key="code" />,
      },
      [TabOption.BROWSER]: {
        name: i18next.t("WORKSPACE$BROWSER_TAB_LABEL"),
        icon: <IoIosGlobe size={18} />,
        component: <Browser key="browser" />,
      },
    }),
    [t],
  );

  return (
    <div className="flex flex-col min-h-0 grow">
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
            tab: "rounded-none border-neutral-600 data-[selected=true]:bg-neutral-800 justify-start",
            tabContent: "group-data-[selected=true]:text-white",
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
      <div className="grow w-full bg-neutral-800 flex min-h-0">
        {tabData[activeTab as TabType].component}
      </div>
    </div>
  );
}
export default Workspace;
