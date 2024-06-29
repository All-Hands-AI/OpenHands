import React from "react";

interface HeaderContentProps {
  title: string;
  subtitle?: string;
}

export function HeaderContent({
  title,
  subtitle = undefined,
}: HeaderContentProps) {
  return (
    <>
      <h3 className="text-foreground">{title}</h3>
      {subtitle && (
        <span className="text-text-editor-base text-sm font-light">
          {subtitle}
        </span>
      )}
    </>
  );
}
