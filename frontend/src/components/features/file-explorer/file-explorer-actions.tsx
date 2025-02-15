import { RefreshIconButton } from "#/components/shared/buttons/refresh-icon-button";
import { ToggleWorkspaceIconButton } from "#/components/shared/buttons/toggle-workspace-icon-button";
import { cn } from "#/utils/utils";

interface ExplorerActionsProps {
  onRefresh: () => void;
  toggleHidden: () => void;
  isHidden: boolean;
}

export function ExplorerActions({
  toggleHidden,
  onRefresh,
  isHidden,
}: ExplorerActionsProps) {
  return (
    <div
      className={cn(
        "flex h-[24px] items-center gap-1",
        isHidden ? "right-3" : "right-2",
      )}
    >
      {!isHidden && <RefreshIconButton onClick={onRefresh} />}

      <ToggleWorkspaceIconButton isHidden={isHidden} onClick={toggleHidden} />
    </div>
  );
}
