import { NavLink } from "@remix-run/react";
import clsx from "clsx";

interface ContainerProps {
  label?: string;
  labels?: { label: string; to: string }[];
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
        <div className="flex border-b border-neutral-600 text-xs font-[500] tracking-[0.01em]">
          {labels.map(({ label: l, to }) => (
            <NavLink
              end
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx("px-4 py-2", !isActive && "text-neutral-400")
              }
            >
              {l}
            </NavLink>
          ))}
        </div>
      )}
      {!labels && label && (
        <div className="px-4 py-2 border-b border-neutral-600 text-xs font-[500] tracking-[0.01em]">
          {label}
        </div>
      )}
      {children}
    </div>
  );
}
