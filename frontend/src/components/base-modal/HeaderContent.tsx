import React from "react";

interface HeaderContentProps {
  title: string;
  subtitle?: string;
}

export const HeaderContent: React.FC<HeaderContentProps> = ({
  title,
  subtitle,
}) => (
  <>
    <h3>{title}</h3>
    {subtitle && (
      <span className="text-neutral-400 text-sm font-light">{subtitle}</span>
    )}
  </>
);

HeaderContent.defaultProps = {
  subtitle: undefined,
};
