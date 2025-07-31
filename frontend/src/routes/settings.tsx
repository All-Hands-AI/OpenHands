import { NavLink, Outlet, redirect } from "react-router";
import { useTranslation } from "react-i18next";
import SettingsIcon from "#/icons/settings.svg?react";
import { cn } from "#/utils/utils";
import { useConfig } from "#/hooks/query/use-config";
import { I18nKey } from "#/i18n/declaration";
import { Route } from "./+types/settings";
import OpenHands from "#/api/open-hands";
import { queryClient } from "#/query-client-config";
import { GetConfigResponse } from "#/api/open-hands.types";

const SAAS_ONLY_PATHS = [
  "/settings/user",
  "/settings/billing",
  "/settings/credits",
  "/settings/api-keys",
];

const SAAS_NAV_ITEMS = [
  { to: "/settings/user", text: "SETTINGS$NAV_USER" },
  { to: "/settings/integrations", text: "SETTINGS$NAV_INTEGRATIONS" },
  { to: "/settings/app", text: "SETTINGS$NAV_APPLICATION" },
  { to: "/settings/billing", text: "SETTINGS$NAV_CREDITS" },
  { to: "/settings/secrets", text: "SETTINGS$NAV_SECRETS" },
  { to: "/settings/api-keys", text: "SETTINGS$NAV_API_KEYS" },
];

const OSS_NAV_ITEMS = [
  { to: "/settings", text: "SETTINGS$NAV_LLM" },
  { to: "/settings/mcp", text: "SETTINGS$NAV_MCP" },
  { to: "/settings/integrations", text: "SETTINGS$NAV_INTEGRATIONS" },
  { to: "/settings/app", text: "SETTINGS$NAV_APPLICATION" },
  { to: "/settings/secrets", text: "SETTINGS$NAV_SECRETS" },
];

export const clientLoader = async ({ request }: Route.ClientLoaderArgs) => {
  const url = new URL(request.url);
  const { pathname } = url;

  let config = queryClient.getQueryData<GetConfigResponse>(["config"]);
  if (!config) {
    config = await OpenHands.getConfig();
    queryClient.setQueryData<GetConfigResponse>(["config"], config);
  }

  const isSaas = config?.APP_MODE === "saas";

  if (isSaas && pathname === "/settings") {
    // no llm settings in saas mode, so redirect to user settings
    return redirect("/settings/user");
  }

  if (!isSaas && SAAS_ONLY_PATHS.includes(pathname)) {
    // if in OSS mode, do not allow access to saas-only paths
    return redirect("/settings");
  }

  return null;
};

function SettingsScreen() {
  const { t } = useTranslation();
  const { data: config } = useConfig();

  const isSaas = config?.APP_MODE === "saas";
  // this is used to determine which settings are available in the UI
  const navItems = isSaas ? SAAS_NAV_ITEMS : OSS_NAV_ITEMS;

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
            <span className="text-[#F9FBFE] text-sm">{t(text)}</span>
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
