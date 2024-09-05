interface ModalBackdropProps {
  children: React.ReactNode;
}

export function ModalBackdrop({ children }: ModalBackdropProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div onClick={(e) => e.stopPropagation()} className="relative">
        {children}
      </div>
    </div>
  );
}
