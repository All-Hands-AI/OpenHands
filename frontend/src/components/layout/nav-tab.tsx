import { NavLink } from "react-router";
import { cn } from "#/utils/utils";
import { BetaBadge } from "./beta-badge";
import { Tooltip } from "@heroui/react";

interface NavTabProps {
  to: string;
  label: string | React.ReactNode;
  icon: React.ReactNode;
  isBeta?: boolean;
  tooltip?: string;
}

export function NavTab({ to, label, icon, isBeta, tooltip }: NavTabProps) {
  const navLink = (
    <NavLink
      end
      key={to}
      to={to}
      className={cn(
        "px-2 border-b border-r border-neutral-600 bg-base-secondary flex-1",
        "first-of-type:rounded-tl-xl last-of-type:rounded-tr-xl last-of-type:border-r-0",
        "flex items-center gap-2",
      )}
    >
      {({ isActive }) => (
        <>
          <div className={cn(isActive && "text-logo")}>{icon}</div>
          {label}
          {isBeta && <BetaBadge />}
        </>
      )}
    </NavLink>
  );

  if (tooltip) {
    return (
      <Tooltip content={tooltip} placement="bottom">
        {navLink}
      </Tooltip>
    );
  }

  return navLink;
}
