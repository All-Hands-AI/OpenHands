import { ContextMenu } from "./context-menu";
import { ContextMenuListItem } from "./context-menu-list-item";
import { ContextMenuSeparator } from "./context-menu-separator";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { useConfig } from "#/hooks/query/use-config";

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
  const { data: config } = useConfig();

  return (
    <ContextMenu
      testId="account-settings-context-menu"
      ref={ref}
      className="absolute left-full -top-1 z-10"
    >
      {config?.APP_MODE === "saas" && config?.APP_SLUG && (
        <a
          href={`https://github.com/apps/${config.APP_SLUG}/installations/new`}
          target="_blank"
          rel="noreferrer noopener"
        >
          <ContextMenuListItem onClick={() => {}}>
            Add More Repositories
          </ContextMenuListItem>
        </a>
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
