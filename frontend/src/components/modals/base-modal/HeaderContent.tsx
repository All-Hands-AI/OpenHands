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
      <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">{title}</h3>
      {subtitle && (
        <span className="text-sm font-light mt-1 text-gray-600 dark:text-gray-400">
          {subtitle}
        </span>
      )}
    </>
  );
}
