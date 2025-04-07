import { NavLink, Outlet } from "react-router";
import SettingsIcon from "#/icons/settings.svg?react";
import { cn } from "#/utils/utils";
import { useConfig } from "#/hooks/query/use-config";
import { BILLING_SETTINGS } from "#/utils/feature-flags";

function SettingsScreen() {
  const { data: config } = useConfig();
  const isSaas = config?.APP_MODE === "saas";

  return (
    <main
      data-testid="settings-screen"
      className="bg-base-secondary border border-tertiary h-full rounded-xl flex flex-col"
    >
      <header className="px-3 py-1.5 border-b border-b-tertiary flex items-center gap-2">
        <SettingsIcon width={16} height={16} />
        <h1 className="text-sm leading-6">Settings</h1>
      </header>

      {isSaas && BILLING_SETTINGS() && (
        <nav
          data-testid="settings-navbar"
          className="flex items-end gap-12 px-11 border-b border-tertiary"
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
              <ul className="text-[#F9FBFE] text-sm">{text}</ul>
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
