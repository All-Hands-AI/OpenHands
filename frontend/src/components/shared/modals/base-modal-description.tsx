import React from "react";

interface BaseModalDescriptionProps {
  children: React.ReactNode;
}

export function BaseModalDescription({ children }: BaseModalDescriptionProps) {
  return (
    <p className="text-sm text-[#A3A3A3]">{children}</p>
  );
}
