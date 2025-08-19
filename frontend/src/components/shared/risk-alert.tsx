import React, { ReactNode } from "react";

interface RiskAlertProps {
  content: ReactNode;
  icon?: ReactNode;
  className?: string;
}

export function RiskAlert({ content, icon, className }: RiskAlertProps) {
  return (
    <div
      className={[
        "bg-red-500/10 border border-red-400/50 text-red-400 rounded-lg px-3 py-2 text-sm",
        className || "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {icon && <span className="mr-1 inline-block align-middle">{icon}</span>}
      <span className="align-middle">{content}</span>
    </div>
  );
}
