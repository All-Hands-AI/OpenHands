import { Tab, Tabs } from "@nextui-org/react";
import React, { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { IoIosGlobe } from "react-icons/io";
import { VscCode } from "react-icons/vsc";
import { useSelector } from "react-redux";
import Calendar from "#/assets/calendar";
import { I18nKey } from "#/i18n/declaration";
import { initialState as initialBrowserState } from "#/state/browserSlice";
import { initialState as initialCodeState } from "#/state/codeSlice";
import { RootState } from "#/store";
import { AllTabs, TabOption, TabType } from "#/types/TabOption";
import Browser from "./Browser";
import CodeEditor from "./CodeEditor";
import Planner from "./Planner";

function Workspace() {
  const { t } = useTranslation();
  const plan = useSelector((state: RootState) => state.plan.plan);
  const code = useSelector((state: RootState) => state.code.code);
  const screenshotSrc = useSelector(
    (state: RootState) => state.browser.screenshotSrc,
  );

  const [activeTab, setActiveTab] = useState<TabType>(TabOption.CODE);
  const [changes, setChanges] = useState<Record<TabType, boolean>>({
    [TabOption.PLANNER]: false,
    [TabOption.CODE]: false,
    [TabOption.BROWSER]: false,
  });

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

  useEffect(() => {
    if (activeTab !== TabOption.PLANNER && plan.mainGoal !== undefined) {
      setChanges((prev) => ({ ...prev, [TabOption.PLANNER]: true }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plan]);

  useEffect(() => {
    if (activeTab !== TabOption.CODE && code !== initialCodeState.code) {
      setChanges((prev) => ({ ...prev, [TabOption.CODE]: true }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plan]);

  useEffect(() => {
    if (
      activeTab !== TabOption.BROWSER &&
      screenshotSrc !== initialBrowserState.screenshotSrc
    ) {
      setChanges((prev) => ({ ...prev, [TabOption.BROWSER]: true }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [screenshotSrc]);

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
            setChanges((prev) => ({ ...prev, [v as TabType]: false }));
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
                  {changes[tab] && (
                    <div className="w-2 h-2 rounded-full animate-pulse bg-blue-500" />
                  )}
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
