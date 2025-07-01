import { NavLink, Outlet, useLocation, useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import React from "react";
import SettingsIcon from "#/icons/settings.svg?react";
import { cn } from "#/utils/utils";
import { useConfig } from "#/hooks/query/use-config";
import { I18nKey } from "#/i18n/declaration";

function SettingsScreen() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { data: config } = useConfig();

  const isSaas = config?.APP_MODE === "saas";

  const saasNavItems = [
    { to: "/settings/user", text: t("SETTINGS$NAV_USER") },
    { to: "/settings/integrations", text: t("SETTINGS$NAV_INTEGRATIONS") },
    { to: "/settings/app", text: t("SETTINGS$NAV_APPLICATION") },
    { to: "/settings/billing", text: t("SETTINGS$NAV_CREDITS") },
    { to: "/settings/secrets", text: t("SETTINGS$NAV_SECRETS") },
    { to: "/settings/api-keys", text: t("SETTINGS$NAV_API_KEYS") },
  ];

  const ossNavItems = [
    { to: "/settings", text: t("SETTINGS$NAV_LLM") },
    { to: "/settings/mcp", text: t("SETTINGS$NAV_MCP") },
    { to: "/settings/integrations", text: t("SETTINGS$NAV_INTEGRATIONS") },
    { to: "/settings/app", text: t("SETTINGS$NAV_APPLICATION") },
    { to: "/settings/secrets", text: t("SETTINGS$NAV_SECRETS") },
  ];

  React.useEffect(() => {
    if (isSaas) {
      if (pathname === "/settings") {
        navigate("/settings/user");
      }
    } else {
      const noEnteringPaths = [
        "/settings/user",
        "/settings/billing",
        "/settings/credits",
        "/settings/api-keys",
      ];
      if (noEnteringPaths.includes(pathname)) {
        navigate("/settings");
      }
    }
  }, [isSaas, pathname]);

  const navItems = isSaas ? saasNavItems : ossNavItems;

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
        className="flex items-end gap-6 px-9 border-b border-tertiary"
      >
        {navItems.map(({ to, text }) => (
          <NavLink
            end
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                "border-b-2 border-transparent py-2.5 px-4 min-w-[40px] flex items-center justify-center",
                isActive && "border-primary",
              )
            }
          >
            <span className="text-[#F9FBFE] text-sm">{text}</span>
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
