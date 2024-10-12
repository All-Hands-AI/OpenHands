import { useClickOutsideElement } from "#/hooks/useClickOutsideElement";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";

interface ProjectMenuCardContextMenuProps {
  isConnectedToGitHub: boolean;
  onConnectToGitHub: () => void;
  onPushToGitHub: () => void;
  onDownloadWorkspace: () => void;
  onClose: () => void;
}

export function ProjectMenuCardContextMenu({
  isConnectedToGitHub,
  onConnectToGitHub,
  onPushToGitHub,
  onDownloadWorkspace,
  onClose,
}: ProjectMenuCardContextMenuProps) {
  const menuRef = useClickOutsideElement<HTMLUListElement>(onClose);

  return (
    <ContextMenu
      ref={menuRef}
      className="absolute right-0 bottom-[calc(100%+8px)]"
    >
      {!isConnectedToGitHub && (
        <ContextMenuListItem onClick={onConnectToGitHub}>
          Connect to GitHub
        </ContextMenuListItem>
      )}
      {isConnectedToGitHub && (
        <ContextMenuListItem onClick={onPushToGitHub}>
          Push to GitHub
        </ContextMenuListItem>
      )}
      <ContextMenuListItem onClick={onDownloadWorkspace}>
        Download as .zip
      </ContextMenuListItem>
    </ContextMenu>
  );
}
