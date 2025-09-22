import { useTranslation } from "react-i18next";
import { TabButton } from "./tab-button";

interface TabNavigationProps {
  activeTab: "system" | "tools";
  onTabChange: (tab: "system" | "tools") => void;
  hasTools: boolean;
}

export function TabNavigation({
  activeTab,
  onTabChange,
  hasTools,
}: TabNavigationProps) {
  const { t } = useTranslation();

  return (
    <div className="flex border-b mb-2" role="tablist">
      <TabButton
        isActive={activeTab === "system"}
        onClick={() => onTabChange("system")}
      >
        {t("SYSTEM_MESSAGE_MODAL$SYSTEM_MESSAGE_TAB")}
      </TabButton>
      {hasTools && (
        <TabButton
          isActive={activeTab === "tools"}
          onClick={() => onTabChange("tools")}
        >
          {t("SYSTEM_MESSAGE_MODAL$TOOLS_TAB")}
        </TabButton>
      )}
    </div>
  );
}
