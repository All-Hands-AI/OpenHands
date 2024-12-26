import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { cn } from "#/utils/utils";
import { ExplorerActions } from "./file-explorer-actions";

interface FileExplorerHeaderProps {
  isOpen: boolean;
  onToggle: () => void;
  onRefreshWorkspace: () => void;
}

export function FileExplorerHeader({
  isOpen,
  onToggle,
  onRefreshWorkspace,
}: FileExplorerHeaderProps) {
  const { t } = useTranslation();

  return (
    <div
      className={cn(
        "sticky top-0 bg-neutral-800",
        "flex items-center",
        !isOpen ? "justify-center" : "justify-between",
      )}
    >
      {isOpen && (
        <div className="text-neutral-300 font-bold text-sm">
          {t(I18nKey.EXPLORER$LABEL_WORKSPACE)}
        </div>
      )}
      <ExplorerActions
        isHidden={!isOpen}
        toggleHidden={onToggle}
        onRefresh={onRefreshWorkspace}
      />
    </div>
  );
}
