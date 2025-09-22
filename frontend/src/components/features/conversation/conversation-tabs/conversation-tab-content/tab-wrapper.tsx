import { ReactNode } from "react";
import { cn } from "#/utils/utils";

interface TabWrapperProps {
  isActive: boolean;
  children: ReactNode;
}

export function TabWrapper({ isActive, children }: TabWrapperProps) {
  return (
    <div className={cn("absolute inset-0", isActive ? "block" : "hidden")}>
      {children}
    </div>
  );
}
