import { NavLink } from "@remix-run/react";
import clsx from "clsx";
import React from "react";

function BetaBadge() {
  return (
    <span className="text-[11px] leading-5 text-root-primary bg-neutral-400 px-1 rounded-xl">
      Beta
    </span>
  );
}

interface ContainerProps {
  label?: string;
  labels?: {
    label: string;
    to: string;
    icon?: React.ReactNode;
    isBeta?: boolean;
  }[];
  children: React.ReactNode;
  className?: React.HTMLAttributes<HTMLDivElement>["className"];
}

export function Container({
  label,
  labels,
  children,
  className,
}: ContainerProps) {
  return (
    <div
      className={clsx(
        "bg-neutral-800 border border-neutral-600 rounded-xl flex flex-col",
        className,
      )}
    >
      {labels && (
        <div className="flex text-xs h-[36px]">
          {labels.map(({ label: l, to, icon, isBeta }) => (
            <NavLink
              end
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  "px-2 border-b border-r border-neutral-600 bg-root-primary flex-1",
                  "first-of-type:rounded-tl-xl last-of-type:rounded-tr-xl last-of-type:border-r-0",
                  "flex items-center gap-2",
                  isActive && "bg-root-secondary",
                )
              }
            >
              {icon}
              {l}
              {isBeta && <BetaBadge />}
            </NavLink>
          ))}
        </div>
      )}
      {!labels && label && (
        <div className="px-2 h-[36px] border-b border-neutral-600 text-xs flex items-center">
          {label}
        </div>
      )}
      <div className="overflow-scroll h-full rounded-b-xl">{children}</div>
    </div>
  );
}
