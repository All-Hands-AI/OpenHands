import { ReactNode } from "react";

interface TabContentAreaProps {
  children: ReactNode;
}

export function TabContentArea({ children }: TabContentAreaProps) {
  return (
    <div className="overflow-hidden flex-grow rounded-b-xl">
      <div className="h-full w-full">
        <div className="h-full w-full relative">{children}</div>
      </div>
    </div>
  );
}
