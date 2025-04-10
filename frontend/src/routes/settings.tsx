import { useConfig } from "#/hooks/query/use-config"
import SettingsIcon from "#/icons/settings.svg?react"
import { cn } from "#/utils/utils"
import { NavLink, Outlet } from "react-router"

function SettingsScreen() {
  const { data: config } = useConfig()
  const isSaas = config?.APP_MODE === "saas"
  const billingIsEnabled = config?.FEATURE_FLAGS.ENABLE_BILLING

  return (
    <main
      data-testid="settings-screen"
      className="flex h-full flex-col bg-neutral-1100 dark:bg-[#080808]"
    >
      <header className="flex items-center gap-2 border-b border-b-neutral-1000 px-3 py-1.5 dark:border-b-[#232521] md:px-5">
        <SettingsIcon width={24} height={24} />
        <h1 className="text-[18px] font-semibold text-neutral-100 dark:text-[#EFEFEF]">
          Settings
        </h1>
      </header>

      {isSaas && billingIsEnabled && (
        <nav
          data-testid="settings-navbar"
          className="flex items-end gap-12 border-b border-[#232521] px-6"
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
              <ul className="text-[14px] font-semibold text-[#EFEFEF]">
                {text}
              </ul>
            </NavLink>
          ))}
        </nav>
      )}

      <div className="flex grow flex-col overflow-auto">
        <Outlet />
      </div>
    </main>
  )
}

export default SettingsScreen
