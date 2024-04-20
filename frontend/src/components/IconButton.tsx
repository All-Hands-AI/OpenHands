import { Button } from "@nextui-org/react";
import React, { MouseEventHandler, ReactElement } from "react";

export interface IconButtonProps {
  icon: ReactElement;
  onClick: MouseEventHandler<HTMLButtonElement>;
  ariaLabel: string;
  testId?: string;
}

function IconButton({
  icon,
  onClick,
  ariaLabel,
  testId,
}: IconButtonProps): React.ReactElement {
  return (
    <Button
      type="button"
      variant="flat"
      onClick={onClick}
      className="cursor-pointer text-[12px] bg-transparent aspect-square px-0 min-w-[20px] h-[20px]"
      aria-label={ariaLabel}
      data-testid={testId}
    >
      {icon}
    </Button>
  );
}

IconButton.defaultProps = {
  testId: "",
};

export default IconButton;
