import { Tab, Tabs } from "@heroui/react";
import { useTranslation } from "react-i18next";
import { MicroagentManagementMicroagents } from "./microagent-management-microagents";
import { MicroagentManagementRepoMicroagents } from "./microagent-management-repo-microagents";
import { I18nKey } from "#/i18n/declaration";

export function MicroagentManagementSidebarTabs() {
  const { t } = useTranslation();

  return (
    <div className="flex w-full flex-col">
      <Tabs
        aria-label="Options"
        classNames={{
          base: "py-6",
          tabList:
            "w-full bg-transparent border border-[#ffffff40] rounded-[6px]",
          tab: "px-2 h-[22px]",
          tabContent: "text-white text-[12px] font-normal",
          panel: "py-0",
          cursor: "bg-[#C9B97480] rounded-sm",
        }}
      >
        <Tab key="personal" title={t(I18nKey.COMMON$PERSONAL)}>
          <MicroagentManagementMicroagents />
        </Tab>
        <Tab key="repositories" title={t(I18nKey.COMMON$REPOSITORIES)}>
          <MicroagentManagementRepoMicroagents />
        </Tab>
        <Tab key="organizations" title={t(I18nKey.COMMON$ORGANIZATIONS)}>
          <MicroagentManagementMicroagents />
        </Tab>
      </Tabs>
    </div>
  );
}
