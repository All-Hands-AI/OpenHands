import { NavLink, Outlet } from "react-router";
import { useTranslation } from "react-i18next";
import SettingsIcon from "#/icons/settings.svg?react";
import { cn } from "#/utils/utils";
import { useConfig } from "#/hooks/query/use-config";
import { I18nKey } from "#/i18n/declaration";

function SettingsScreen() {
  const { t } = useTranslation();
  const { data: config } = useConfig();

  const isSaas = config?.APP_MODE === "saas";
  const billingIsEnabled = config?.FEATURE_FLAGS.ENABLE_BILLING;

  const navItems = [
    { to: "/settings", text: "LLM" },
    { to: "/settings/github", text: "GitHub" },
    { to: "/settings/app", text: "Application" },
    { to: "/settings/secrets", text: "Secrets" },
    // Only show Credits tab if the app is in SaaS mode
    ...(isSaas && billingIsEnabled
      ? [{ to: "/settings/billing", text: "Credits" }]
      : []),
  ];

  return (
    <main
      data-testid="settings-screen"
      className="bg-base-secondary border border-tertiary h-full rounded-xl flex flex-col"
    >
      <header className="px-3 py-1.5 border-b border-b-tertiary flex items-center gap-2">
        <SettingsIcon width={16} height={16} />
        <h1 className="text-sm leading-6">{t(I18nKey.SETTINGS$TITLE)}</h1>
      </header>

      <nav
        data-testid="settings-navbar"
        className="flex items-end gap-12 px-11 border-b border-tertiary"
      >
        {navItems.map(({ to, text }) => (
          <NavLink
            end
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                "border-b-2 border-transparent py-2.5",
                isActive && "border-primary",
              )
            }
          >
            <ul className="text-[#F9FBFE] text-sm">{text}</ul>
          </NavLink>
        ))}
      </nav>

      <div className="flex flex-col grow overflow-auto">
        <Outlet />
      </div>
    </main>
  );
}

export default SettingsScreen;
