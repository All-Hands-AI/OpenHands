import React from "react";

interface ModalBackdropProps {
  children: React.ReactNode;
  onClose?: () => void;
}

export function ModalBackdrop({ children, onClose }: ModalBackdropProps) {
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose?.();
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, []);

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center"
    >
      <div onClick={(e) => e.stopPropagation()} className="relative">
        {children}
      </div>
    </div>
  );
}
