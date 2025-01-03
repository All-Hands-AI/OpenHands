import { useTranslation } from "react-i18next";
import { ContextMenu } from "./context-menu";
import { ContextMenuListItem } from "./context-menu-list-item";
import { ContextMenuSeparator } from "./context-menu-separator";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { I18nKey } from "#/i18n/declaration";

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
  const { t } = useTranslation();

  return (
    <ContextMenu
      testId="account-settings-context-menu"
      ref={ref}
      className="absolute left-full -top-1 z-10"
    >
      <ContextMenuListItem onClick={onClickAccountSettings}>
        {t(I18nKey.ACCOUNT_SETTINGS$SETTINGS)}
      </ContextMenuListItem>
      <ContextMenuSeparator />
      <ContextMenuListItem onClick={onLogout} isDisabled={!isLoggedIn}>
        {t(I18nKey.ACCOUNT_SETTINGS$LOGOUT)}
      </ContextMenuListItem>
    </ContextMenu>
  );
}
