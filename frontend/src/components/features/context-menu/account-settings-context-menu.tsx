import { ContextMenu } from "./context-menu";
import { ContextMenuListItem } from "./context-menu-list-item";
import { ContextMenuSeparator } from "./context-menu-separator";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { useConfig } from "#/hooks/query/use-config";

interface AccountSettingsContextMenuProps {
  onAddMoreRepositories: () => void;
  onClickAccountSettings: () => void;
  onLogout: () => void;
  onClose: () => void;
  isLoggedIn: boolean;
}

export function AccountSettingsContextMenu({
  onAddMoreRepositories,
  onClickAccountSettings,
  onLogout,
  onClose,
  isLoggedIn,
}: AccountSettingsContextMenuProps) {
  const ref = useClickOutsideElement<HTMLUListElement>(onClose);
  const { data: config } = useConfig();

  return (
    <ContextMenu
      testId="account-settings-context-menu"
      ref={ref}
      className="absolute left-full -top-1 z-10"
    >
      {config?.APP_MODE === "saas" && (
        <ContextMenuListItem onClick={onAddMoreRepositories}>
          Add More Repositories
        </ContextMenuListItem>
      )}
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
