import { Tab, Tabs } from "@heroui/react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { MicroagentManagementRepositories } from "./microagent-management-repositories";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";

export function MicroagentManagementSidebarTabs() {
  const { t } = useTranslation();

  const { repositories, personalRepositories, organizationRepositories } =
    useSelector((state: RootState) => state.microagentManagement);

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
          panel: "p-0",
          cursor: "bg-[#C9B97480] rounded-sm",
        }}
      >
        <Tab key="personal" title={t(I18nKey.COMMON$PERSONAL)}>
          <MicroagentManagementRepositories
            repositories={personalRepositories}
            tabType="personal"
          />
        </Tab>
        <Tab key="repositories" title={t(I18nKey.COMMON$REPOSITORIES)}>
          <MicroagentManagementRepositories
            repositories={repositories}
            tabType="repositories"
          />
        </Tab>
        <Tab key="organizations" title={t(I18nKey.COMMON$ORGANIZATIONS)}>
          <MicroagentManagementRepositories
            repositories={organizationRepositories}
            tabType="organizations"
          />
        </Tab>
      </Tabs>
    </div>
  );
}
