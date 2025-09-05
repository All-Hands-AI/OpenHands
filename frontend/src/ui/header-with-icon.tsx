import { ReactNode } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "#/utils/utils";

const headerWithIconVariants = cva("flex items-center", {
  variants: {
    gap: {
      default: "gap-[10px]",
    },
    textSize: {
      default: "text-base",
    },
    fontWeight: {
      default: "font-bold",
    },
    textColor: {
      default: "text-white",
    },
    lineHeight: {
      default: "leading-5",
    },
  },
  defaultVariants: {
    gap: "default",
    textSize: "default",
    fontWeight: "default",
    textColor: "default",
    lineHeight: "default",
  },
});

interface HeaderWithIconProps
  extends VariantProps<typeof headerWithIconVariants> {
  icon: ReactNode;
  children: ReactNode;
  className?: string;
}

export function HeaderWithIcon({
  icon,
  children,
  className = "",
  gap,
  textSize,
  fontWeight,
  textColor,
  lineHeight,
}: HeaderWithIconProps) {
  return (
    <div
      className={cn(
        headerWithIconVariants({
          gap,
          textSize,
          fontWeight,
          textColor,
          lineHeight,
        }),
        className,
      )}
    >
      {icon}
      <span
        className={cn(
          headerWithIconVariants({
            lineHeight,
            textSize,
            fontWeight,
            textColor,
          }),
          "flex items-center",
        )}
      >
        {children}
      </span>
    </div>
  );
}
