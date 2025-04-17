import { NavLink } from "react-router";
import { cn } from "#/utils/utils";
import { BetaBadge } from "./beta-badge";
import { LoadingSpinner } from "../shared/loading-spinner";

interface NavTabProps {
  to: string;
  label: string | React.ReactNode;
  icon: React.ReactNode;
  isBeta?: boolean;
  isLoading?: boolean;
}

export function NavTab({ to, label, icon, isBeta, isLoading }: NavTabProps) {
  return (
    <NavLink
      end
      key={to}
      to={to}
      className={cn(
        "px-2 border-b border-r border-neutral-600 bg-base-secondary flex-1",
        "first-of-type:rounded-tl-xl last-of-type:rounded-tr-xl last-of-type:border-r-0",
        "flex items-center gap-2 h-full min-h-[36px]",
      )}
    >
      {({ isActive }) => (
        <>
          <div className="flex items-center gap-2">
            <div className={cn(isActive && "text-logo")}>{icon}</div>
            {label}
            {isBeta && <BetaBadge />}
          </div>

          {isLoading && <LoadingSpinner size="small" />}
        </>
      )}
    </NavLink>
  );
}
