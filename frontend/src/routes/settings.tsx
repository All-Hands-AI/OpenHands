import { NavLink, Outlet } from "react-router";
import SettingsIcon from "#/icons/settings.svg?react";
import { cn } from "#/utils/utils";
import { useConfig } from "#/hooks/query/use-config";

function SettingsScreen() {
  const { data: config } = useConfig();
  const isSaas = config?.APP_MODE === "saas";
  const billingIsEnabled = config?.FEATURE_FLAGS.ENABLE_BILLING;

  return (
    <main
      data-testid="settings-screen"
      className="bg-[#080808] h-full flex flex-col"
    >
      <header className="px-3 md:px-5 py-1.5 border-b border-b-[#232521] flex items-center gap-2">
        <SettingsIcon width={24} height={24} />
        <h1 className="text-[18px] font-semibold text-[#EFEFEF]">Settings</h1>
      </header>

      {isSaas && billingIsEnabled && (
        <nav
          data-testid="settings-navbar"
          className="flex items-end gap-12 px-6 border-b border-[#232521]"
        >
          {[
            { to: "/settings", text: "Account" },
            { to: "/settings/billing", text: "Credits" },
          ].map(({ to, text }) => (
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
              <ul className="text-[#EFEFEF] font-semibold text-[14px]">
                {text}
              </ul>
            </NavLink>
          ))}
        </nav>
      )}

      <div className="flex flex-col grow overflow-auto">
        <Outlet />
      </div>
    </main>
  );
}

export default SettingsScreen;
