import { useMemo } from "react";
import { NavLink, Outlet, redirect, useLocation } from "react-router";
import { useTranslation } from "react-i18next";
import SettingsIcon from "#/icons/settings-gear.svg?react";
import { useConfig } from "#/hooks/query/use-config";
import { I18nKey } from "#/i18n/declaration";
import { Route } from "./+types/settings";
import OptionService from "#/api/option-service/option-service.api";
import { queryClient } from "#/query-client-config";
import { ProPill } from "#/components/features/settings/pro-pill";
import { GetConfigResponse } from "#/api/option-service/option.types";
import { useSubscriptionAccess } from "#/hooks/query/use-subscription-access";
import { SAAS_NAV_ITEMS, OSS_NAV_ITEMS } from "#/constants/settings-nav";
import CircuitIcon from "#/icons/u-circuit.svg?react";
import { Typography } from "#/ui/typography";
import { cn } from "#/utils/utils";

const SAAS_ONLY_PATHS = [
  "/settings/user",
  "/settings/billing",
  "/settings/credits",
  "/settings/api-keys",
];

export const clientLoader = async ({ request }: Route.ClientLoaderArgs) => {
  const url = new URL(request.url);
  const { pathname } = url;

  let config = queryClient.getQueryData<GetConfigResponse>(["config"]);
  if (!config) {
    config = await OptionService.getConfig();
    queryClient.setQueryData<GetConfigResponse>(["config"], config);
  }

  const isSaas = config?.APP_MODE === "saas";

  if (!isSaas && SAAS_ONLY_PATHS.includes(pathname)) {
    // if in OSS mode, do not allow access to saas-only paths
    return redirect("/settings");
  }

  return null;
};

function SettingsScreen() {
  const { t } = useTranslation();
  const { data: config } = useConfig();
  const { data: subscriptionAccess } = useSubscriptionAccess();
  const location = useLocation();

  const isSaas = config?.APP_MODE === "saas";
  // this is used to determine which settings are available in the UI
  const navItems = useMemo(() => {
    const items = [];
    if (isSaas) {
      if (subscriptionAccess) {
        items.push({
          icon: <CircuitIcon width={22} height={22} />,
          to: "/settings",
          text: "SETTINGS$NAV_LLM",
        });
      }
      items.push(...SAAS_NAV_ITEMS);
    } else {
      items.push(...OSS_NAV_ITEMS);
    }
    return items;
  }, [isSaas, !!subscriptionAccess]);

  const currentSectionTitle = useMemo(() => {
    const currentItem = navItems.find((item) => item.to === location.pathname);
    return currentItem ? currentItem.text : "SETTINGS$NAV_LLM"; // fallback for default route
  }, [navItems, location.pathname]);

  return (
    <main
      data-testid="settings-screen"
      className="bg-base-secondary rounded-xl h-full flex flex-col px-[14px] pt-8"
    >
      <div className="flex flex-1 overflow-hidden gap-10">
        <nav data-testid="settings-navbar" className="flex flex-col w-64 gap-6">
          <div className="flex items-center gap-2 ml-1.5">
            <SettingsIcon width={16} height={16} />
            <Typography.H2>{t(I18nKey.SETTINGS$TITLE)}</Typography.H2>
          </div>
          <div className="flex flex-col gap-2">
            {navItems.map(({ to, text, icon }) => (
              <NavLink
                end
                key={to}
                to={to}
                className={({ isActive }) =>
                  cn(
                    "p-1 flex items-center gap-3 rounded-md",
                    isActive && "bg-[#454545]",
                  )
                }
              >
                {icon}
                <Typography.Text className="text-[#A3A3A3]">
                  {t(text)}
                </Typography.Text>
                {isSaas && to === "/settings" && <ProPill className="ml-2" />}
              </NavLink>
            ))}
          </div>
        </nav>

        <div className="flex flex-col flex-1 overflow-auto gap-6">
          <Typography.H2>{t(currentSectionTitle)}</Typography.H2>
          <div className="flex-1 overflow-auto">
            <Outlet />
          </div>
        </div>
      </div>
    </main>
  );
}

export default SettingsScreen;
