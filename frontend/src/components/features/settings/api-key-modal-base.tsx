import React, { ReactNode } from "react";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";

interface ApiKeyModalBaseProps {
  isOpen: boolean;
  title: string;
  width?: string;
  children: ReactNode;
  footer: ReactNode;
}

export function ApiKeyModalBase({
  isOpen,
  title,
  width = "500px",
  children,
  footer,
}: ApiKeyModalBaseProps) {
  if (!isOpen) return null;

  return (
    <ModalBackdrop>
      <div
        className="bg-base-secondary p-6 rounded-xl flex flex-col gap-4 border border-tertiary"
        style={{ width }}
      >
        <h3 className="text-xl font-bold">{title}</h3>
        {children}
        <div className="w-full flex gap-2 mt-2">{footer}</div>
      </div>
    </ModalBackdrop>
  );
}
