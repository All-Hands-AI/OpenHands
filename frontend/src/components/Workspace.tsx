import { Tab, Tabs } from "@nextui-org/react";
import React, { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { IoIosGlobe } from "react-icons/io";
import { VscCode, VscListOrdered } from "react-icons/vsc";
import { useSelector } from "react-redux";
import { I18nKey } from "#/i18n/declaration";
import { initialState as initialCodeState } from "#/state/codeSlice";
import { RootState } from "#/store";
import { TabOption, TabType } from "#/types/TabOption";
import Browser from "./Browser";
import CodeEditor from "./file-explorer/CodeEditor";
import Planner, { isAddTaskAction } from "./Planner";
import Jupyter from "./Jupyter";
import { getSettings } from "#/services/settings";
import { useSession } from "#/context/session";
import { extractJupyterCells } from "#/utils/extractJupyterCells";

function Workspace() {
  const { t } = useTranslation();
  const code = useSelector((state: RootState) => state.code.code);

  const { eventLog } = useSession();
  const [task, setTask] = React.useState<AddTaskAction | undefined>(undefined);

  React.useEffect(() => {
    const addTaskAction = eventLog
      .map((msg) => JSON.parse(msg))
      .find(isAddTaskAction);

    if (addTaskAction) {
      setTask(addTaskAction);
    }
  }, [eventLog]);

  const { AGENT } = getSettings();
  const baseTabs = [TabOption.CODE, TabOption.BROWSER];
  const extraTabsMap: { [key: string]: TabOption[] } = {
    CodeActAgent: [TabOption.JUPYTER],
    PlannerAgent: [TabOption.PLANNER],
  };
  const extraTabs = extraTabsMap[AGENT] || [];
  const showTabs = [...baseTabs, ...extraTabs];

  // FIXME: Type this
  const [jupyterCells, setJupyterCells] = React.useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<TabType>(TabOption.CODE);
  const [changes, setChanges] = useState<Record<TabType, boolean>>({
    [TabOption.PLANNER]: false,
    [TabOption.CODE]: false,
    [TabOption.BROWSER]: false,
    [TabOption.JUPYTER]: false,
  });

  React.useEffect(() => {
    const cells = extractJupyterCells(eventLog.map((msg) => JSON.parse(msg)));
    setJupyterCells(cells);
  }, [eventLog]);

  const iconSize = 18;
  const tabData = useMemo(
    () => ({
      [TabOption.PLANNER]: {
        name: t(I18nKey.WORKSPACE$PLANNER_TAB_LABEL),
        icon: <VscListOrdered size={iconSize} />,
        component: <Planner key="planner" />,
      },
      [TabOption.CODE]: {
        name: t(I18nKey.WORKSPACE$CODE_EDITOR_TAB_LABEL),
        icon: <VscCode size={iconSize} />,
        component: <CodeEditor key="code" />,
      },
      [TabOption.BROWSER]: {
        name: t(I18nKey.WORKSPACE$BROWSER_TAB_LABEL),
        icon: <IoIosGlobe size={iconSize} />,
        component: <Browser key="browser" />,
      },
      [TabOption.JUPYTER]: {
        name: t(I18nKey.WORKSPACE$JUPYTER_TAB_LABEL),
        icon: <VscCode size={iconSize} />,
        component: <Jupyter key="jupyter" />,
      },
    }),
    [t],
  );

  useEffect(() => {
    if (activeTab !== TabOption.PLANNER && task) {
      setChanges((prev) => ({ ...prev, [TabOption.PLANNER]: true }));
    }
  }, [task]);

  useEffect(() => {
    if (activeTab !== TabOption.CODE && code !== initialCodeState.code) {
      setChanges((prev) => ({ ...prev, [TabOption.CODE]: true }));
    }
  }, [task]);

  useEffect(() => {
    if (activeTab !== TabOption.JUPYTER && jupyterCells.length > 0) {
      // FIXME: This is a temporary solution to show the jupyter tab when the first cell is added
      // Only need to show the tab only when a cell is added
      setChanges((prev) => ({ ...prev, [TabOption.JUPYTER]: true }));
    }
  }, [activeTab, jupyterCells]);

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
          {showTabs.map((tab, index) => (
            <Tab
              key={tab}
              className={`flex-grow ${index + 1 === showTabs.length ? "" : "border-r"}`}
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
