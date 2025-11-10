import { ReactNode } from "react";

interface TabContentAreaProps {
  children: ReactNode;
}

export function TabContentArea({ children }: TabContentAreaProps) {
  return (
    <div className="overflow-hidden flex-grow rounded-b-xl h-full w-full relative">
      {children}
    </div>
  );
}
