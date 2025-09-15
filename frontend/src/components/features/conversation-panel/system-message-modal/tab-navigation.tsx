import { useTranslation } from "react-i18next";
import { cn } from "#/utils/utils";

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
    <div className="flex border-b mb-2">
      <button
        type="button"
        className={cn(
          "px-4 py-2 font-medium border-b-2 transition-colors",
          activeTab === "system"
            ? "border-primary text-gray-100"
            : "border-transparent hover:text-gray-700 dark:hover:text-gray-300",
        )}
        onClick={() => onTabChange("system")}
      >
        {t("SYSTEM_MESSAGE_MODAL$SYSTEM_MESSAGE_TAB")}
      </button>
      {hasTools && (
        <button
          type="button"
          className={cn(
            "px-4 py-2 font-medium border-b-2 transition-colors",
            activeTab === "tools"
              ? "border-primary text-gray-100"
              : "border-transparent hover:text-gray-700 dark:hover:text-gray-300",
          )}
          onClick={() => onTabChange("tools")}
        >
          {t("SYSTEM_MESSAGE_MODAL$TOOLS_TAB")}
        </button>
      )}
    </div>
  );
}
