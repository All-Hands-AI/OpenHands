import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { ContextMenu } from "./context-menu";
import { ContextMenuListItem } from "./context-menu-list-item";
import { ContextMenuSeparator } from "./context-menu-separator";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { useConfig } from "#/hooks/query/use-config";
import { I18nKey } from "#/i18n/declaration";
import CreditCardIcon from "#/icons/credit-card.svg?react";
import KeyIcon from "#/icons/key.svg?react";
import LogOutIcon from "#/icons/log-out.svg?react";
import ServerProcessIcon from "#/icons/server-process.svg?react";
import SettingsGearIcon from "#/icons/settings-gear.svg?react";
import CircuitIcon from "#/icons/u-circuit.svg?react";
import PuzzlePieceIcon from "#/icons/u-puzzle-piece.svg?react";
import UserIcon from "#/icons/user.svg?react";

interface AccountSettingsContextMenuProps {
  onLogout: () => void;
  onClose: () => void;
}

const SAAS_NAV_ITEMS = [
  {
    icon: <UserIcon width={16} height={16} />,
    to: "/settings/user",
    text: "COMMON$USER_SETTINGS",
  },
  {
    icon: <PuzzlePieceIcon width={16} height={16} />,
    to: "/settings/integrations",
    text: "SETTINGS$NAV_INTEGRATIONS",
  },
  {
    icon: <SettingsGearIcon width={16} height={16} />,
    to: "/settings/app",
    text: "COMMON$APPLICATION_SETTINGS",
  },
  {
    icon: <CreditCardIcon width={16} height={16} />,
    to: "/settings/billing",
    text: "SETTINGS$NAV_CREDITS",
  },
  {
    icon: <KeyIcon width={16} height={16} />,
    to: "/settings/secrets",
    text: "SETTINGS$NAV_SECRETS",
  },
  {
    icon: <KeyIcon width={16} height={16} />,
    to: "/settings/api-keys",
    text: "SETTINGS$NAV_API_KEYS",
  },
];

const OSS_NAV_ITEMS = [
  {
    icon: <CircuitIcon width={16} height={16} />,
    to: "/settings",
    text: "COMMON$LANGUAGE_MODEL_LLM",
  },
  {
    icon: <ServerProcessIcon width={16} height={16} />,
    to: "/settings/mcp",
    text: "COMMON$MODEL_CONTEXT_PROTOCOL_MCP",
  },
  {
    icon: <PuzzlePieceIcon width={16} height={16} />,
    to: "/settings/integrations",
    text: "SETTINGS$NAV_INTEGRATIONS",
  },
  {
    icon: <SettingsGearIcon width={16} height={16} />,
    to: "/settings/app",
    text: "COMMON$APPLICATION_SETTINGS",
  },
  {
    icon: <KeyIcon width={16} height={16} />,
    to: "/settings/secrets",
    text: "SETTINGS$NAV_SECRETS",
  },
];

export function AccountSettingsContextMenu({
  onLogout,
  onClose,
}: AccountSettingsContextMenuProps) {
  const ref = useClickOutsideElement<HTMLUListElement>(onClose);
  const { t } = useTranslation();
  const { data: config } = useConfig();

  const isSaas = config?.APP_MODE === "saas";
  const navItems = isSaas ? SAAS_NAV_ITEMS : OSS_NAV_ITEMS;

  const handleNavigationClick = () => {
    onClose();
    // The Link component will handle the actual navigation
  };

  return (
    <ContextMenu
      testId="account-settings-context-menu"
      ref={ref}
      className="absolute right-0 md:right-full md:left-full mt-2 md:mt-0 md:bottom-0 ml-2 z-10 w-fit bg-tertiary rounded-[6px] p-[6px]"
    >
      {navItems.map(({ to, text, icon }) => (
        <Link key={to} to={to} className="text-decoration-none">
          <ContextMenuListItem
            onClick={() => handleNavigationClick()}
            className="flex items-center gap-2 p-2 hover:bg-[#5C5D62] rounded"
          >
            {icon}
            <span className="text-white text-sm">{t(text)}</span>
          </ContextMenuListItem>
        </Link>
      ))}

      <ContextMenuSeparator className="bg-[#959CB2] my-[6px]" />

      <ContextMenuListItem
        onClick={onLogout}
        className="flex items-center gap-2 p-2 hover:bg-[#5C5D62] rounded"
      >
        <LogOutIcon width={16} height={16} />
        <span className="text-white text-sm">
          {t(I18nKey.ACCOUNT_SETTINGS$LOGOUT)}
        </span>
      </ContextMenuListItem>
    </ContextMenu>
  );
}
