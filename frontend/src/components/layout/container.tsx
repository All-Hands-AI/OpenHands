import clsx from "clsx";
import React from "react";
import { NavTab } from "./nav-tab";

interface ContainerProps {
  label?: string;
  labels?: {
    id: string;
    label: string;
    icon?: React.ReactNode;
    isBeta?: boolean;
    isActive: boolean;
    onClick: (id: string) => void;
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
          {labels.map(({ id, label: l, icon, isBeta, isActive, onClick }) => (
            <NavTab key={id} id={id} label={l} icon={icon} isBeta={isBeta} isActive={isActive} onClick={onClick} />
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
