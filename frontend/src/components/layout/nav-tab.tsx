import { cn } from "#/utils/utils";
import { NavLink } from "react-router";
import { BetaBadge } from "./beta-badge";

interface NavTabProps {
  to: string;
  label: string | React.ReactNode;
  icon: React.ReactNode;
  isBeta?: boolean;
}

export function NavTab({ to, label, icon, isBeta }: NavTabProps) {
  return (
    <NavLink
      end
      key={to}
      to={to}
      className={({ isActive }) =>
        cn(
          "px-2 border-b border-r border-gray-200 bg-gray-300 flex-1",
          "first-of-type:rounded-tl-xl last-of-type:rounded-tr-xl last-of-type:border-r-0",
          "flex items-center gap-2",
          isActive && "bg-gray-400 border-b-transparent border-l-transparent",
        )
      }
    >
      {({ isActive }) => (
        <>
          <div className={cn(isActive && "text-white")}>{icon}</div>
          <span className={cn(isActive && "text-white font-medium")}>
            {label}
          </span>
          {isBeta && <BetaBadge />}
        </>
      )}
    </NavLink>
  );
}
