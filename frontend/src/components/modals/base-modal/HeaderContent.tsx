import React from "react";

interface HeaderContentProps {
  maintitle: string;
  subtitle?: string;
}

export function HeaderContent({
  maintitle,
  subtitle = undefined,
}: HeaderContentProps) {
  return (
    <>
      <h3>{maintitle}</h3>
      {subtitle && (
        <span className="text-neutral-400 text-sm font-light">{subtitle}</span>
      )}
    </>
  );
}
