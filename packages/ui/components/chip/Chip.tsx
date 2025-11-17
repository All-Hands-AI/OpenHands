import { type PropsWithChildren } from "react";
import type { BaseProps, HTMLProps } from "../../shared/types";
import { cn } from "../../shared/utils/cn";
import { Typography } from "../typography/Typography";
import { chipStyles, type ChipColor, type ChipVariant } from "./utils";

export type ChipProps = Omit<HTMLProps<"div">, "label"> & {
  color?: ChipColor;
  variant?: ChipVariant;
} & BaseProps;

export const Chip = ({
  className,
  color = "gray",
  variant = "pill",
  children,
  testId,
  ...props
}: PropsWithChildren<ChipProps>) => {
  return (
    <div
      {...props}
      data-testid={testId}
      className={cn(
        "flex flex-row items-center px-1.5 py-1",
        variant === "pill" ? "rounded-full" : "rounded-lg",
        "border-1",
        chipStyles[color],
        className
      )}
    >
      <Typography.Text fontSize="xs" fontWeight={500} className="text-inherit">
        {children}
      </Typography.Text>
    </div>
  );
};
