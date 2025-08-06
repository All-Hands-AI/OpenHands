import clsx from "clsx";
import React, { ComponentType } from "react";
import { NavTab } from "./nav-tab";
import { cn } from "#/utils/utils";

interface ContainerProps {
  label?: React.ReactNode;
  labels?: {
    to: string;
    icon: ComponentType<{ className: string }>;
    rightContent?: React.ReactNode;
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
        "bg-base-secondary border border-neutral-600 rounded-xl flex flex-col h-full w-full",
        className,
      )}
    >
      {labels && (
        <div
          className={cn(
            "relative w-full p-2",
            "flex flex-row justify-end items-center gap-4.5",
          )}
        >
          {labels.map(({ to, icon, rightContent }) => (
            <NavTab key={to} to={to} icon={icon} rightContent={rightContent} />
          ))}
        </div>
      )}
      {!labels && label && (
        <div className="px-2 h-[36px] border-b border-neutral-600 text-xs flex items-center">
          {label}
        </div>
      )}
      <div className="overflow-hidden flex-grow rounded-b-xl">{children}</div>
    </div>
  );
}
