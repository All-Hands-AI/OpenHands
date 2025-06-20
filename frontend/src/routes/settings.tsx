import { NavLink, Outlet, useLocation, useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import React from "react";
import SettingsIcon from "#/icons/settings.svg?react";
import { cn } from "#/utils/utils";
import { useConfig } from "#/hooks/query/use-config";
import { I18nKey } from "#/i18n/declaration";
import { FiGitBranch, FiSettings, FiCreditCard, FiShield, FiKey, FiCpu, FiDatabase } from "react-icons/fi";

function SettingsScreen() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { data: config } = useConfig();

  const isSaas = config?.APP_MODE === "saas";

  const saasNavItems = [
    { to: "/settings/git", text: t("SETTINGS$NAV_GIT"), icon: FiGitBranch },
    { to: "/settings/app", text: t("SETTINGS$NAV_APPLICATION"), icon: FiSettings },
    { to: "/settings/billing", text: t("SETTINGS$NAV_CREDITS"), icon: FiCreditCard },
    { to: "/settings/secrets", text: t("SETTINGS$NAV_SECRETS"), icon: FiShield },
    { to: "/settings/api-keys", text: t("SETTINGS$NAV_API_KEYS"), icon: FiKey },
  ];

  const ossNavItems = [
    { to: "/settings", text: t("SETTINGS$NAV_LLM"), icon: FiCpu },
    { to: "/settings/mcp", text: t("SETTINGS$NAV_MCP"), icon: FiDatabase },
    { to: "/settings/git", text: t("SETTINGS$NAV_GIT"), icon: FiGitBranch },
    { to: "/settings/app", text: t("SETTINGS$NAV_APPLICATION"), icon: FiSettings },
    { to: "/settings/secrets", text: t("SETTINGS$NAV_SECRETS"), icon: FiShield },
  ];

  React.useEffect(() => {
    if (isSaas) {
      if (pathname === "/settings") {
        navigate("/settings/git");
      }
    } else {
      const noEnteringPaths = [
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
    <div
      className="h-full rounded-xl flex"
      data-testid="settings-container"
    >
      {/* Left Sidebar Navigation */}
      <div className="w-64 p-6">
        <header className="flex items-center gap-2 mb-6">
          <SettingsIcon width={16} height={16} className="text-[#F3CE49]" />
          <h1 className="text-sm leading-6 text-content font-semibold">{t(I18nKey.SETTINGS$TITLE)}</h1>
        </header>

        <nav
          data-testid="settings-navbar"
          className="flex flex-col gap-1"
        >
          {navItems.map(({ to, text, icon: Icon }) => (
            <NavLink
              end
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 text-content-secondary text-sm py-2 px-1 rounded transition-colors",
                  isActive
                    ? "bg-tertiary text-content"
                    : "hover:bg-tertiary hover:text-content"
                )
              }
            >
              <Icon className="w-4 h-4" />
              {text}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-auto">
        <Outlet />
      </div>
    </div>
  );
}

export default SettingsScreen;
