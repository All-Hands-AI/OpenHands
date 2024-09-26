import React from "react";
import { ContextMenu } from "./context-menu/context-menu";
import { ContextMenuListItem } from "./context-menu/context-menu-list-item";
import { ContextMenuSeparator } from "./context-menu/context-menu-separator";

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
  const menuRef = React.useRef<HTMLUListElement>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, []);

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
