import { ContextMenu } from "./context-menu/context-menu";
import { ContextMenuListItem } from "./context-menu/context-menu-list-item";
import { ContextMenuSeparator } from "./context-menu/context-menu-separator";
import { useClickOutsideElement } from "#/hooks/useClickOutsideElement";

interface AccountSettingsContextMenuProps {
  onClickAccountSettings: () => void;
  onLogout: () => void;
  onClose: () => void;
  isLoggedIn: boolean;
}

export function AccountSettingsContextMenu({
  onClickAccountSettings,
  onLogout,
  onClose,
  isLoggedIn,
}: AccountSettingsContextMenuProps) {
  const ref = useClickOutsideElement<HTMLUListElement>(onClose);

  return (
    <ContextMenu ref={ref} className="absolute left-full -top-1 z-10">
      <ContextMenuListItem onClick={onClickAccountSettings}>
        Account Settings
      </ContextMenuListItem>
      <ContextMenuSeparator />
      <ContextMenuListItem onClick={onLogout} isDisabled={!isLoggedIn}>
        Logout
      </ContextMenuListItem>
    </ContextMenu>
  );
}
