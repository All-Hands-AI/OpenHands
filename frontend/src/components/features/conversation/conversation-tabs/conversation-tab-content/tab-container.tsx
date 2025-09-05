import { ReactNode } from "react";
import { cn } from "#/utils/utils";

interface TabContainerProps {
  children: ReactNode;
}

export function TabContainer({ children }: TabContainerProps) {
  return (
    <div
      className={cn(
        "bg-[#25272D] border border-[#525252] rounded-xl flex flex-col h-full w-full",
        "h-full w-full",
      )}
    >
      {children}
    </div>
  );
}
