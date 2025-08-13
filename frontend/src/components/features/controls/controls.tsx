import { SecurityLock } from "./security-lock";

interface ControlsProps {
  setSecurityOpen: (isOpen: boolean) => void;
  showSecurityLock: boolean;
}

export function Controls({ setSecurityOpen, showSecurityLock }: ControlsProps) {
  return (
    <div className="flex flex-col gap-2 md:items-center md:justify-between md:flex-row">
      <div className="flex items-center gap-2">
        {showSecurityLock && (
          <SecurityLock onClick={() => setSecurityOpen(true)} />
        )}
      </div>
    </div>
  );
}
