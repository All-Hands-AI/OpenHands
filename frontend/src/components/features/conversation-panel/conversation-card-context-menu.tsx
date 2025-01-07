import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";

interface ConversationCardContextMenuProps {
  onClose: () => void;
  onDelete: (event: React.MouseEvent<HTMLButtonElement>) => void;
}

export function ConversationCardContextMenu({
  onClose,
  onDelete,
}: ConversationCardContextMenuProps) {
  const ref = useClickOutsideElement<HTMLUListElement>(onClose);

  return (
    <ContextMenu
      ref={ref}
      testId="context-menu"
      className="left-full float-right"
    >
      <ContextMenuListItem testId="delete-button" onClick={onDelete}>
        Delete
      </ContextMenuListItem>
    </ContextMenu>
  );
}
