import clsx from "clsx";
import React from "react";

interface ModalBodyProps {
  testID?: string;
  children: React.ReactNode;
  className?: React.HTMLProps<HTMLDivElement>["className"];
}

function ModalBody({ testID, children, className }: ModalBodyProps) {
  return (
    <div
      data-testid={testID}
      className={clsx(
        "bg-root-primary flex flex-col gap-6 items-center w-[384px] p-6 rounded-xl",
        className,
      )}
    >
      {children}
    </div>
  );
}

export default ModalBody;
