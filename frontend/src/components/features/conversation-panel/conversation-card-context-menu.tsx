import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { cn } from "#/utils/utils";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";

interface ConversationCardContextMenuProps {
  onClose: () => void;
  onDelete?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onEdit?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onDownload?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  position?: "top" | "bottom";
}

export function ConversationCardContextMenu({
  onClose,
  onDelete,
  onEdit,
  onDownload,
  position = "bottom",
}: ConversationCardContextMenuProps) {
  const ref = useClickOutsideElement<HTMLUListElement>(onClose);

  return (
    <ContextMenu
      ref={ref}
      testId="context-menu"
      className={cn(
        "right-0 absolute",
        position === "top" && "bottom-full",
        position === "bottom" && "top-full",
      )}
    >
      {onDelete && (
        <ContextMenuListItem testId="delete-button" onClick={onDelete}>
          Delete
        </ContextMenuListItem>
      )}
      {onEdit && (
        <ContextMenuListItem testId="edit-button" onClick={onEdit}>
          Edit Title
        </ContextMenuListItem>
      )}
      {onDownload && (
        <ContextMenuListItem testId="download-button" onClick={onDownload}>
          Download Workspace
        </ContextMenuListItem>
      )}
    </ContextMenu>
  );
}
