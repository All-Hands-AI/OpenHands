import { cn } from "#/utils/utils";
import { RefreshIconButton } from "../../ui/buttons/refresh-icon-button";
import { ToggleWorkspaceIconButton } from "../../ui/buttons/toggle-workspace-icon-button";
import { UploadIconButton } from "../../ui/buttons/upload-icon-button";

interface ExplorerActionsProps {
  onRefresh: () => void;
  onUpload: () => void;
  toggleHidden: () => void;
  isHidden: boolean;
}

export function ExplorerActions({
  toggleHidden,
  onRefresh,
  onUpload,
  isHidden,
}: ExplorerActionsProps) {
  return (
    <div
      className={cn(
        "flex h-[24px] items-center gap-1",
        isHidden ? "right-3" : "right-2",
      )}
    >
      {!isHidden && (
        <>
          <RefreshIconButton onClick={onRefresh} />
          <UploadIconButton onClick={onUpload} />
        </>
      )}

      <ToggleWorkspaceIconButton isHidden={isHidden} onClick={toggleHidden} />
    </div>
  );
}
