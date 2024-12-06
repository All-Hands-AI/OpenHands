import { IoLockClosed } from "react-icons/io5";

interface SecurityLockProps {
  onClick: () => void;
}

export function SecurityLock({ onClick }: SecurityLockProps) {
  return (
    <div
      className="cursor-pointer hover:opacity-80 transition-all"
      style={{ marginRight: "8px" }}
      onClick={onClick}
    >
      <IoLockClosed size={20} />
    </div>
  );
}
