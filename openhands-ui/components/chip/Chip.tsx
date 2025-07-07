import { type PropsWithChildren } from "react";
import type { HTMLProps } from "../../shared/types";
import { cn } from "../../shared/utils/cn";
import { Typography } from "../typography/Typography";
import { chipStyles, type ChipColor, type ChipVariant } from "./utils";
import { invariant } from "../../shared/utils/invariant";

export type ChipProps = Omit<HTMLProps<"div">, "label"> & {
  color?: ChipColor;
  variant?: ChipVariant;
};

export const Chip = ({
  className,
  color = "gray",
  variant = "pill",
  children,
  ...props
}: PropsWithChildren<ChipProps>) => {
  invariant(typeof children === "string", "Children must be string");

  return (
    <div
      {...props}
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
