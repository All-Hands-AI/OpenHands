import clsx from "clsx"
import React from "react"
import { NavTab } from "./nav-tab"

interface ContainerProps {
  label?: React.ReactNode
  labels?: {
    label: string | React.ReactNode
    to: string
    icon?: React.ReactNode
    isBeta?: boolean
  }[]
  children: React.ReactNode
  className?: React.HTMLAttributes<HTMLDivElement>["className"]
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
        "flex flex-col rounded-xl border border-gray-200 bg-gray-300",
        className,
      )}
    >
      {labels && (
        <div className="flex h-12 text-xs">
          {labels.map(({ label: l, to, icon, isBeta }) => (
            <NavTab key={to} to={to} label={l} icon={icon} isBeta={isBeta} />
          ))}
        </div>
      )}
      {!labels && label && (
        <div className="flex h-12 items-center border-b border-gray-200 px-2 text-xs">
          {label}
        </div>
      )}
      <div className="h-full overflow-hidden">{children}</div>
    </div>
  )
}
