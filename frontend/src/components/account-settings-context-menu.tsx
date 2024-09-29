import { ContextMenu } from "./context-menu/context-menu";
import { ContextMenuListItem } from "./context-menu/context-menu-list-item";
import { ContextMenuSeparator } from "./context-menu/context-menu-separator";
import { useClickOutsideElement } from "#/hooks/useClickOutsideElement";

interface AccountSettingsContextMenuProps {
  isLoggedIn: boolean;
  onClickAccountSettings: () => void;
  onLogout: () => void;
  onClose: () => void;
}

export function AccountSettingsContextMenu({
  isLoggedIn,
  onClickAccountSettings,
  onLogout,
  onClose,
}: AccountSettingsContextMenuProps) {
  const menuRef = useClickOutsideElement<HTMLUListElement>(onClose);

  return (
    <ContextMenu ref={menuRef} className="absolute left-full -top-1 z-10">
      <ContextMenuListItem onClick={onClickAccountSettings}>
        Account Settings
      </ContextMenuListItem>
      {isLoggedIn && (
        <>
          <ContextMenuSeparator />
          <ContextMenuListItem onClick={onLogout}>Logout</ContextMenuListItem>
        </>
      )}
    </ContextMenu>
  );
}
