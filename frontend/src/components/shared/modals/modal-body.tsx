import React from "react";
import { cn } from "#/utils/utils";

interface ModalBodyProps {
  testID?: string;
  children: React.ReactNode;
  className?: React.HTMLProps<HTMLDivElement>["className"];
}

export function ModalBody({ testID, children, className }: ModalBodyProps) {
  return (
    <div
      data-testid={testID}
      className={cn(
        "bg-base flex flex-col gap-6 items-center w-[384px] p-6 rounded-xl",
        className,
      )}
    >
      {children}
    </div>
  );
}
