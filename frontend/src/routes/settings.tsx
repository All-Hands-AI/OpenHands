import { NavLink, Outlet, redirect, useLocation } from "react-router";
import { useTranslation } from "react-i18next";
import SettingsIcon from "#/icons/settings.svg?react";
import { cn } from "#/utils/utils";
import { useConfig } from "#/hooks/query/use-config";
import { I18nKey } from "#/i18n/declaration";
import { Route } from "./+types/settings";
import OpenHands from "#/api/open-hands";
import { queryClient } from "#/query-client-config";
import { GetConfigResponse } from "#/api/open-hands.types";
import { useOrganizations } from "#/hooks/query/use-organizations";
import { useSelectedOrganizationId } from "#/context/use-selected-organization";
import { useMe } from "#/hooks/query/use-me";
import { SettingsDropdownInput } from "#/components/features/settings/settings-dropdown-input";

const SAAS_ONLY_PATHS = [
  "/settings/user",
  "/settings/billing",
  "/settings/credits",
  "/settings/api-keys",
  "/settings/team",
  "/settings/org",
];

const SAAS_NAV_ITEMS = [
  { to: "/settings/user", text: "SETTINGS$NAV_USER" },
  { to: "/settings/integrations", text: "SETTINGS$NAV_INTEGRATIONS" },
  { to: "/settings/app", text: "SETTINGS$NAV_APPLICATION" },
  { to: "/settings/billing", text: "SETTINGS$NAV_CREDITS" },
  { to: "/settings/secrets", text: "SETTINGS$NAV_SECRETS" },
  { to: "/settings/api-keys", text: "SETTINGS$NAV_API_KEYS" },
  { to: "/settings/team", text: "Team" },
  { to: "/settings/org", text: "Organization" },
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
  const { orgId, setOrgId } = useSelectedOrganizationId();
  const { data: me } = useMe();
  const { data: organizations } = useOrganizations();
  const { data: config } = useConfig();
  const location = useLocation();

  const isSaas = config?.APP_MODE === "saas";
  const isUser = me?.role === "user";
  // this is used to determine which settings are available in the UI
  const navItems = isSaas ? SAAS_NAV_ITEMS : OSS_NAV_ITEMS;

  return (
    <main
      data-testid="settings-screen"
      className="bg-base-secondary border border-tertiary h-full rounded-xl flex"
    >
      <div className="w-64 border-r border-tertiary flex flex-col">
        <header className="px-3 py-1.5 border-b border-b-tertiary flex items-center gap-2">
          <SettingsIcon width={16} height={16} />
          <h1 className="text-sm leading-6">{t(I18nKey.SETTINGS$TITLE)}</h1>
        </header>

        <div className="px-3 py-2 border-b border-tertiary">
          <SettingsDropdownInput
            testId="org-select"
            name="organization"
            placeholder="Please select an organization"
            selectedKey={orgId || ""}
            items={
              organizations?.map((org) => ({
                key: org.id,
                label: org.name,
              })) || []
            }
            onSelectionChange={(org) => {
              if (org) {
                setOrgId(org.toString());
              } else {
                setOrgId(null);
              }
            }}
          />
        </div>

        <nav data-testid="settings-navbar" className="flex flex-col gap-1 p-2">
          {navItems
            .filter((navItem) => {
              // if user is not an admin or no org is selected, do not show team/org settings
              if (
                (navItem.to === "/settings/team" ||
                  navItem.to === "/settings/org") &&
                (isUser || !orgId)
              ) {
                return false;
              }

              return true;
            })
            .map(({ to, text }) => (
              <NavLink
                end
                key={to}
                to={to}
                className={({ isActive }) =>
                  cn(
                    "py-2 px-3 rounded flex items-center text-sm",
                    isActive ? "bg-base text-white" : "hover:bg-tertiary",
                  )
                }
              >
                <span>{t(text)}</span>
              </NavLink>
            ))}
        </nav>
      </div>

      <div className="flex flex-col grow overflow-auto">
        <header className="px-11 pt-4">
          <h1 className="text-2xl font-semibold text-white">
            {t(
              navItems.find((item) => item.to === location.pathname)?.text ||
                "",
            )}
          </h1>
        </header>
        <div>
          <Outlet />
        </div>
      </div>
    </main>
  );
}

export default SettingsScreen;
