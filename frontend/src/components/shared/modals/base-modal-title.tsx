import React from "react";

interface BaseModalTitleProps {
  title: string;
}

export function BaseModalTitle({ title }: BaseModalTitleProps) {
  return (
    <h2 className="text-xl font-semibold -tracking-[0.01em]">{title}</h2>
  );
}
